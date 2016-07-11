from flask import Flask, request, jsonify
from pymongo import MongoClient
import pymongo.errors
from datetime import datetime
from voluptuous import Schema, Coerce, All, Range, MultipleInvalid
from bson.objectid import ObjectId
from bson.errors import InvalidId
import pika
import settings
import logging
from structlog import wrap_logger

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


def get_db_responses():
    mongo_client = MongoClient(app.config['MONGODB_URL'])
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


def queue_notification(notification, bound_logger):
    bound_logger.debug(" [x] Queuing notification to " + settings.RABBIT_QUEUE)
    bound_logger.debug(notification)
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_URL))
    channel = connection.channel()
    channel.queue_declare(queue=settings.RABBIT_QUEUE)
    channel.basic_publish(exchange='',
                          routing_key=settings.RABBIT_QUEUE,
                          body=notification)
    bound_logger.debug(" [x] Queued notification to " + settings.RABBIT_QUEUE)
    connection.close()


def save_response(survey_response, bound_logger):
    doc = {}
    doc['survey_response'] = survey_response
    doc['added_date'] = datetime.utcnow()
    try:
        result = get_db_responses().insert_one(doc)
        return str(result.inserted_id)

    except pymongo.errors.OperationFailure as e:
        bound_logger.error("MongoDB failed", error=str(e))
        return None


@app.route('/responses', methods=['POST'])
def do_save_response():
    survey_response = request.get_json(force=True)
    metadata = survey_response['metadata']
    bound_logger = logger.bind(user_id=metadata['user_id'], ru_ref=metadata['ru_ref'])

    inserted_id = save_response(survey_response, bound_logger)
    if inserted_id is None:
        return server_error("Unable to save response")

    queue_notification(inserted_id, bound_logger)
    return jsonify(result="ok")


@app.route('/responses', methods=['GET'])
def do_get_responses():
    try:
        schema(request.args)
    except MultipleInvalid as e:
        logger.error("Multiple Invalid", error=str(e))
        return client_error(str(e))

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
        document['added_ms'] = int(document['added_date'].strftime("%s")) * 1000
        responses.append(document)

    results['results'] = responses
    return jsonify(results)


@app.route('/responses/<mongo_id>', methods=['GET'])
def do_get_response(mongo_id):
    try:
        result = get_db_responses().find_one({"_id": ObjectId(mongo_id)})
        if result:
            result['_id'] = str(result['_id'])
            return jsonify(result)

    except InvalidId as e:
        logger.error("Invalid ID", status='404')
        return jsonify({}), 404

    except Exception as e:
        logger.error("Exception", status='404')
        raise e

    return jsonify({}), 404

if __name__ == '__main__':
    logger.debug("START")
    app.run(debug=True, host='0.0.0.0', port=5000)
