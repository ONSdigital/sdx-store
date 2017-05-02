from datetime import datetime
import json
import logging
import logging.handlers
import os

from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from structlog import wrap_logger
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.exc import SQLAlchemyError
from voluptuous import Schema, Coerce, All, Range
from werkzeug.exceptions import BadRequest

from queue_publisher import QueuePublisher
import settings

__version__ = "1.4.1"

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS

db = SQLAlchemy(app=app)

schema = Schema({
    'survey_id': str,
    'form': str,
    'ru_ref': str,
    'period': str,
    'added_ms': Coerce(int),
    'per_page': All(Coerce(int), Range(min=1, max=100)),
    'page': All(Coerce(int), Range(min=1))
})


class InvalidUsageError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class SurveyResponse(db.Model):
    __tablename__ = 'responses'
    tx_id = db.Column("tx_id", UUID, primary_key=True)
    ts = db.Column("ts", db.TIMESTAMP(timezone=True),
                   server_default=db.func.now(),
                   onupdate=db.func.now())
    invalid = db.Column("invalid", db.Boolean)
    data = db.Column("data", JSONB)

    def __init__(self, tx_id, invalid, data):
        self.tx_id = tx_id
        self.invalid = invalid
        self.data = data


def create_tables():
    db.create_all()


def get_responses(tx_id=None, invalid_flag=None):
    try:
        r = SurveyResponse.query.filter_by(tx_id=tx_id, invalid=invalid_flag).all()
        logger.info("Retrieved results from db", tx_id=tx_id, invalid_flag=invalid_flag)
        return r
    except SQLAlchemyError as e:
        logger.error("Could not retrieve results from db", tx_id=tx_id, invalid_flag=invalid_flag)
        return None


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def json_response(content):
    output = json.dumps(object_as_dict(content), default=json_serial)
    return Response(output, mimetype='application/json')


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def queue_cs_notification(logger, tx_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CS_QUEUE)
    return publisher.publish_message(tx_id)


def queue_ctp_notification(logger, tx_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CTP_QUEUE)
    return publisher.publish_message(tx_id)


def queue_cora_notification(logger, tx_id):
    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_CORA_QUEUE)
    return publisher.publish_message(tx_id)


def save_response(bound_logger, survey_response):
    invalid = survey_response.get("invalid")

    try:
        tx_id = survey_response["tx_id"]
    except KeyError:
        raise InvalidUsageError("Missing transaction id. Unable to save response",
                                500)
    else:
        response = SurveyResponse(tx_id=tx_id,
                                  invalid=invalid,
                                  data=survey_response)
        try:
            db.session.add(response)
            db.session.commit()
        except SQLAlchemyError as e:
            raise server_error("Unable to save response")
        else:
            bound_logger.info("Response saved",
                              inserted_id=tx_id,
                              invalid=invalid)
        return invalid


@app.errorhandler(500)
def server_error(error=None):
    logger.error(error, status=500)
    message = {
        'status': 500,
        'message': error,
    }

    resp = jsonify(message)
    resp.status_code = 500
    return resp


@app.errorhandler(InvalidUsageError)
def invalid_usage_error(error=None):
    logger.error(error.message, status=500)
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/responses', methods=['POST'])
def do_save_response():
    try:
        survey_response = request.get_json(force=True)
    except BadRequest:
        msg = "Invalid POST request to /response"
        raise InvalidUsageError(msg, status_code=400)

    metadata = survey_response['metadata']

    bound_logger = logger.bind(user_id=metadata['user_id'],
                               ru_ref=metadata['ru_ref'],
                               tx_id=survey_response['tx_id'])

    invalid = save_response(bound_logger, survey_response)

    if invalid is True:
        return jsonify(result="false")

    tx_id = survey_response['tx_id']

    if survey_response['survey_id'] == 'census':
        queued = queue_ctp_notification(bound_logger, tx_id)
    elif survey_response['survey_id'] == '144':
        queued = queue_cora_notification(bound_logger, tx_id)
    else:
        queued = queue_cs_notification(bound_logger, tx_id)

    if not queued:
        return server_error("Unable to queue notification")
    return jsonify(result="ok")


@app.route('/invalid-responses', methods=['GET'])
def do_get_invalid_responses():
    responses = get_responses(invalid_flag=True)

    if responses:
        jsonify(responses)
    else:
        return jsonify({}), 404


@app.route('/responses', methods=['GET'])
def do_get_responses():
    return jsonify(get_responses(invalid_flag=False))


@app.route('/responses/<tx_id>', methods=['GET'])
def do_get_response(tx_id):
    result = get_responses(tx_id=tx_id)
    if result:
        r = [object_as_dict(r) for r in result]
        tx_id = result[0].tx_id
        return jsonify(r)
    else:
        logger.warning("Could not retrieve response", tx_id=tx_id)
        return jsonify({}), 404


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
        return server_error("Unable to queue response")

    return jsonify(result="ok")


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})


if __name__ == '__main__':
    # Startup
    logger.info("Starting server", version=__version__)
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
