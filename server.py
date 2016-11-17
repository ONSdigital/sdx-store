import json
import logging.handlers
import os
from datetime import datetime

from flask import Flask, request, jsonify, Response
from structlog import wrap_logger
from voluptuous import Schema, Coerce, All, Range, MultipleInvalid

import settings
import pg
from queue_publisher import QueuePublisher

logger = wrap_logger(logging.getLogger(__name__))
app = Flask(__name__)

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


def queue_notification(logger, response_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_QUEUE)
    return publisher.publish_message(response_id)


@app.route('/responses', methods=['POST'])
def do_save_response():
    survey_response = request.get_json(force=True)
    metadata = survey_response['metadata']
    bound_logger = logger.bind(user_id=metadata['user_id'], ru_ref=metadata['ru_ref'])

    inserted_id = pg.save_response(survey_response, bound_logger)

    if inserted_id is None:
        return server_error("Unable to save response")

    queued = queue_notification(bound_logger, inserted_id)
    if queued is False:
        return server_error("Unable to queue notification")

    return jsonify(result="ok")


def get_search_criteria(page, per_page):
    return {
        "page": page,
        "items_per_page": per_page,

        "query": {"json": True,
                  "path": '',
                  "operator": "eq",
                  "value": 0}
    }


@app.before_first_request
def _run_on_start():
    pg.create_table()


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

    search_criteria = get_search_criteria(page, per_page)

    if survey_id:
        search_criteria['query'].update({'path': 'survey_id', 'value': survey_id})
    if form:
        search_criteria['query'].update({'path': 'form', 'value': form})
    if ru_ref:
        search_criteria['query'].update({'path': '{metadata, ru_ref}', 'value': json.dumps(ru_ref)})
    if period:
        search_criteria['query'].update({'path': '{collection, period}', 'value': json.dumps(period)})

    if added_ms:
        search_criteria['query'].update({'json': False, 'path': 'added_date', 'operator': 'gte',
                                         'value': datetime.fromtimestamp(int(added_ms) / 1000.0)})

    # select all responses
    if not search_criteria['query']['path']:
        search_criteria['query'].update({'json': False, 'path': 'id', 'operator': 'gt', 'value': 0})

    results = {}
    responses = []

    results['total_hits'] = pg.count(search_criteria)

    cursor = pg.search(search_criteria)

    for item in cursor:
        document = item[2]
        document['_id'] = str(item[0])
        if added_ms:
            document['added_ms'] = int(item[1].strftime("%s")) * 1000
        responses.append(document)

    results['results'] = responses
    return json_response(results)


@app.route('/responses/<response_id>', methods=['GET'])
def do_get_response(response_id):
    try:
        isinstance(int(response_id), int)
    except ValueError:
        return jsonify({}), 400

    try:
        with pg.db() as cursor:
            cursor.execute(pg.SQL['SELECT_EQ_ID'], (int(response_id),))

            result = cursor.fetchone()

            if result:
                result = json.loads(result[2])
                result['_id'] = response_id
                return json_response(result)

    except Exception as e:
        return server_error(repr(e))

    return jsonify({}), 404


@app.route('/queue', methods=['POST'])
def do_queue():
    response_id = request.get_json(force=True)['id']
    # check document exists with id
    result = do_get_response(response_id)
    if result.status_code != 200:
        return result

    queued = queue_notification(logger, response_id)
    if queued is False:
        return server_error("Unable to queue notification")

    return jsonify(result="ok")


if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    logger.debug("START")

    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
