import settings
import logging
import logging.handlers
from flask import Flask, request, jsonify, Response
import json
from pymongo import MongoClient
import pymongo.errors
from datetime import datetime
from voluptuous import Schema, Coerce, All, Range, MultipleInvalid
from bson.objectid import ObjectId
from bson.errors import InvalidId
from structlog import wrap_logger
from queue_publisher import QueuePublisher
import os

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))
app = Flask(__name__)
app.config['MONGODB_URL'] = settings.MONGODB_URL

schema = Schema({
    'survey_id': str,
    'form': str,
    'ru_ref': str,
    'period': str,
    'added_ms': Coerce(int),
    'per_page': All(Coerce(int), Range(min=1, max=100)),
    'page': All(Coerce(int), Range(min=1))
})


def get_db_responses(invalid_flag=False):
    mongo_client = MongoClient(app.config['MONGODB_URL'])
    if invalid_flag:
        return mongo_client.sdx_store.invalid_responses

    return mongo_client.sdx_store.responses


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
    doc = {}
    doc['survey_response'] = survey_response
    doc['added_date'] = datetime.utcnow()

    invalid_flag = False

    if 'invalid' in survey_response:
        invalid_flag = survey_response['invalid']

    try:
        result = get_db_responses(invalid_flag).insert_one(doc)
        bound_logger.info("Response saved", inserted_id=result.inserted_id, invalid=invalid_flag)
        return str(result.inserted_id), invalid_flag

    except pymongo.errors.OperationFailure as e:
        bound_logger.error("Failed to store survey response", exception=str(e))
        return None, False


def queue_cs_notification(logger, mongo_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CS_QUEUE)
    return publisher.publish_message(mongo_id)


def queue_ctp_notification(logger, mongo_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CTP_QUEUE)
    return publisher.publish_message(mongo_id)


def queue_cora_notification(logger, mongo_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CORA_QUEUE)
    return publisher.publish_message(mongo_id)


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


@app.route('/responses', methods=['GET'])
def do_get_responses():
    try:
        schema(request.args)
    except MultipleInvalid as e:
        logger.error("Request args failed schema validation", error=str(e))
        return client_error(repr(e))

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
    db_responses = get_db_responses()
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


@app.route('/responses/<mongo_id>', methods=['GET'])
def do_get_response(mongo_id):
    try:
        result = get_db_responses().find_one({"_id": ObjectId(mongo_id)})
        if result:
            result['_id'] = str(result['_id'])
            return json_response(result)

    except InvalidId as e:
        return client_error(repr(e))

    except Exception as e:
        return server_error(repr(e))

    return jsonify({}), 404


@app.route('/queue', methods=['POST'])
def do_queue():
    mongo_id = request.get_json(force=True)['id']
    # check document exists with id
    result = do_get_response(mongo_id)
    if result.status_code != 200:
        return result

    response = json.loads(result.response[0].decode('utf-8'))

    if response['survey_response']['survey_id'] == 'census':
        queued = queue_ctp_notification(logger, mongo_id)
    elif response['survey_response']['survey_id'] == '144':
        queued = queue_cora_notification(logger, mongo_id)
    else:
        queued = queue_cs_notification(logger, mongo_id)

    if queued is False:
        return server_error("Unable to queue notification")

    return jsonify(result="ok")


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})


if __name__ == '__main__':
    # Startup
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
