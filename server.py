import settings
import logging
import logging.handlers
from flask import Flask, request, jsonify, Response
import json
from datetime import datetime
from voluptuous import Schema, Coerce, All, Range, MultipleInvalid
from bson.objectid import ObjectId
from bson.errors import InvalidId
from structlog import wrap_logger
from queue_publisher import QueuePublisher
import os

from pgstore import get_dsn
from pgstore import ResponseStore
from pgstore import ProcessSafePoolManager

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))

app = Flask(__name__)
pm = ProcessSafePoolManager(**get_dsn(settings))

def create_tables():
    con = pm.getconn()
    ResponseStore.Creation().run(con)
    pm.putconn(con)

def get_db_responses(logger=None, invalid_flag=False):
    try:
        con = pm.getconn()
        return ResponseStore.Filter(valid=not invalid_flag).run(con, logger)
    finally:
        pm.putconn(con)

schema = Schema({
    'survey_id': str,
    'form': str,
    'ru_ref': str,
    'period': str,
    'added_ms': Coerce(int),
    'per_page': All(Coerce(int), Range(min=1, max=100)),
    'page': All(Coerce(int), Range(min=1))
})


@app.errorhandler(400)
def errorhandler_400(e):
    return client_error(repr(e))


def client_error(error=None):
    logger.error(error, status=400)
    message = {
        'status': 400,
        'message': error,
        'uri': request.url
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def errorhandler_500(e):
    return server_error(repr(e))


@app.errorhandler(500)
def server_error(error=None):
    logger.error(error, status=500)
    message = {
        'status': 500,
        'message': error
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def json_response(content):
    output = json.dumps(content, default=json_serial)
    return Response(output, mimetype='application/json')


def save_response(bound_logger, survey_response):

    con = pm.getconn()
    invalid = survey_response.get("invalid")
    try:
        id_ = ResponseStore.Insertion(
            id=survey_response["tx_id"],
            valid=not invalid,
            data=survey_response
        ).run(con, log=bound_logger)
    except KeyError:
        bound_logger.warning("Missing transaction id")
        return None, False
    else:
        bound_logger.info("Response saved", inserted_id=id_, invalid=invalid)
        return id_, invalid
    finally:
        pm.putconn(con)



def queue_cs_notification(logger, tx_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CS_QUEUE)
    return publisher.publish_message(tx_id)


def queue_ctp_notification(logger, tx_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CTP_QUEUE)
    return publisher.publish_message(tx_id)


def queue_cora_notification(logger, tx_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CORA_QUEUE)
    return publisher.publish_message(tx_id)


@app.route('/responses', methods=['POST'])
def do_save_response():
    survey_response = request.get_json(force=True)
    metadata = survey_response['metadata']
    bound_logger = logger.bind(user_id=metadata['user_id'], ru_ref=metadata['ru_ref'], tx_id=survey_response['tx_id'])

    inserted_id, invalid_flag = save_response(bound_logger, survey_response)
    if inserted_id is None:
        return server_error("Unable to save response")

    if invalid_flag is True:
        return jsonify(result="false")

    if survey_response['survey_id'] == 'census':
        queued = queue_ctp_notification(bound_logger, inserted_id)
    elif survey_response['survey_id'] == '144':
        queued = queue_cora_notification(bound_logger, inserted_id)
    else:
        queued = queue_cs_notification(bound_logger, inserted_id)

    if queued is False:
        return server_error("Unable to queue notification")

    return jsonify(result="ok")


def fetch_responses(invalid=False):
    try:
        schema(request.args)
    except MultipleInvalid as e:
        logger.error("Request args failed schema validation", error=str(e))
        return client_error(repr(e))

    if invalid:
        invalid = True

    survey_id = request.args.get('survey_id')
    form = request.args.get('form')
    ru_ref = request.args.get('ru_ref')
    period = request.args.get('period')
    added_ms = request.args.get('added_ms')
    page = request.args.get('page')
    per_page = request.args.get('per_page')

    # paging defaults
    if not page:
        page = 1
    else:
        page = int(page)
    if not per_page:
        per_page = 100
    else:
        per_page = int(per_page)

    search_criteria = {}
    if survey_id:
        search_criteria['survey_response.survey_id'] = survey_id
    if form:
        search_criteria['survey_response.form'] = form
    if ru_ref:
        search_criteria['survey_response.metadata.ru_ref'] = ru_ref
    if period:
        search_criteria['survey_response.collection.period'] = period
    if added_ms:
        search_criteria['added_date'] = {
            "$gte": datetime.fromtimestamp(int(added_ms) / 1000.0)
        }

    results = {}
    responses = []
    db_responses = get_db_responses(invalid_flag=invalid)
    count = db_responses.find(search_criteria).count()
    results['total_hits'] = count
    cursor = db_responses.find(search_criteria).skip(per_page * (page - 1)).limit(per_page)
    for document in cursor:
        document['_id'] = str(document['_id'])
        if added_ms:
            document['added_ms'] = int(document['added_date'].strftime("%s")) * 1000
        responses.append(document)

    results['results'] = responses
    return json_response(results)


@app.route('/invalid-responses', methods=['GET'])
def do_get_invalid_responses():
    return fetch_responses(True)


@app.route('/responses', methods=['GET'])
def do_get_responses():
    return fetch_responses(False)


@app.route('/responses/<tx_id>', methods=['GET'])
def do_get_response(tx_id):
    if not (tx_id and ResponseStore.idPattern.match(tx_id)):
        return client_error("Invalid transaction_id: {0}".format(tx_id))

    try:
        con = pm.getconn()
        result = ResponseStore.Selection(id=tx_id).run(con, logger)
        if result:
            return json_response(result["data"])
        else:
            return jsonify({}), 404

    except Exception as e:
        return server_error(repr(e))

    finally:
        pm.putconn(con)


@app.route('/queue', methods=['POST'])
def do_queue():
    tx_id = request.get_json(force=True)['id']
    # check document exists with id
    result = do_get_response(tx_id)
    if result.status_code != 200:
        return result

    response = json.loads(result.response[0].decode('utf-8'))

    if response['survey_response']['survey_id'] == 'census':
        queued = queue_ctp_notification(logger, tx_id)
    elif response['survey_response']['survey_id'] == '144':
        queued = queue_cora_notification(logger, tx_id)
    else:
        queued = queue_cs_notification(logger, tx_id)

    if queued is False:
        return server_error("Unable to queue notification")

    return jsonify(result="ok")


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})


if __name__ == '__main__':
    # Startup
    port = int(os.getenv("PORT"))
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=port)
