from datetime import datetime
import json
import logging
import logging.handlers
import os

from flask import jsonify, Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from sdx.common.logger_config import logger_initial_config
from sqlalchemy import inspect, select, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from structlog import wrap_logger
from voluptuous import All, Coerce, MultipleInvalid, Range, Schema
from werkzeug.exceptions import BadRequest

from queue_publisher import Publisher
import settings


__version__ = "2.1.0"

logger_initial_config(service_name='sdx-store', log_level=settings.LOGGING_LEVEL)
logger = wrap_logger(logging.getLogger(__name__))

publisher = Publisher(logger)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS

db = SQLAlchemy(app=app)

schema = Schema({
    'added_ms': Coerce(int),
    'form': str,
    'page': All(Coerce(int), Range(min=1)),
    'period': str,
    'per_page': All(Coerce(int), Range(min=1, max=100)),
    'ru_ref': str,
    'survey_id': str,
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
    tx_id = db.Column("tx_id",
                      UUID,
                      primary_key=True)

    ts = db.Column("ts",
                   db.TIMESTAMP(timezone=True),
                   server_default=db.func.now(),
                   onupdate=db.func.now())

    invalid = db.Column("invalid",
                        db.Boolean,
                        default=False)

    data = db.Column("data", JSONB)

    def __init__(self, tx_id, invalid, data):
        self.tx_id = tx_id
        self.invalid = invalid
        self.data = data

    def __repr__(self):
        return '<SurveyResponse {}>'.format(self.tx_id)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class FeedbackResponse(db.Model):
    __tablename__ = "feedback_responses"
    id = db.Column("id",
                   Integer,
                   primary_key=True)

    ts = db.Column("ts",
                   db.TIMESTAMP(timezone=True),
                   server_default=db.func.now(),
                   onupdate=db.func.now())

    invalid = db.Column("invalid",
                        db.Boolean,
                        default=False)

    data = db.Column("data", JSONB)

    survey = db.Column("survey", String(length=25))

    period = db.Column("period", String(length=25))

    def __init__(self, invalid, data, survey, period):
        self.invalid = invalid
        self.data = data
        self.survey = survey
        self.period = period


def create_tables():
    logger.info("Creating tables")
    db.create_all()


def get_responses(tx_id=None, invalid=None):
    try:
        schema(request.args)
    except MultipleInvalid:
        raise InvalidUsageError("Request args failed schema validation",
                                status_code=400,
                                payload=request.args)

    page = request.args.get('page')
    per_page = request.args.get('per_page')

    if not page:
        page = 1
    else:
        page = int(page)
    if not per_page:
        per_page = 100
    else:
        per_page = int(per_page)

    kwargs = {k: v for k, v in {'tx_id': tx_id, 'invalid': invalid}.items() if v is not None}

    try:
        r = SurveyResponse.query.filter_by(**kwargs).paginate(page, per_page)
        logger.info("Retrieved results from db", tx_id=tx_id, invalid=invalid)
        return r
    except SQLAlchemyError as e:
        logger.error("Could not retrieve results from db",
                     tx_id=tx_id,
                     invalid=invalid,
                     error=e)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def json_response(content):
    output = json.dumps(object_as_dict(content), default=json_serial)
    return Response(output, mimetype='application/json')


def merge(response):
    try:
        db.session.merge(response)
        db.session.commit()
    except IntegrityError as e:
        logger.error("Integrity error in database. Rolling back commit",
                     error=e)
        db.session.rollback()
        raise e
    except SQLAlchemyError as e:
        logger.error("Unable to save response", error=e)
        db.session.rollback()
        raise e
    else:
        logger.info("Response saved", tx_id=response.tx_id)


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def save_response(bound_logger, survey_response):
    bound_logger.info("Saving response")
    invalid = survey_response.get("invalid")

    try:
        tx_id = survey_response["tx_id"]
    except KeyError:
        raise InvalidUsageError("Missing transaction id. Unable to save response",
                                400)

    response = SurveyResponse(tx_id=tx_id,
                              invalid=invalid,
                              data=survey_response)

    merge(response)
    return invalid


def save_feedback_response(bound_logger, survey_feedback_response):
    bound_logger.info("Saving feedback response")
    invalid = survey_feedback_response.get("invalid")
    survey = survey_feedback_response.get("survey_type")
    period = survey_feedback_response.get("survey_period")

    feedback_response = FeedbackResponse(invalid=invalid,
                                         data=survey_feedback_response,
                                         survey=survey,
                                         period=period)

    try:
        db.session.add(feedback_response)
        db.session.commit()
    except IntegrityError as e:
        logger.error("Integrity error in database. Rolling back commit", error=e)
        db.session.rollback()
        raise e
    except SQLAlchemyError as e:
        logger.error("Unable to save response", error=e)
        db.session.rollback()
        raise e
    else:
        logger.info("Feedback response saved")

    return invalid


def test_sql(connection):
    """Run a SELECT 1 to test the database connection"""
    logger.debug("Executing select 1")
    connection.scalar(select([1]))


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
    logger.error(error.message, status=400, payload=error.payload)
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/responses', methods=['POST'])
def do_save_response():
    try:
        survey_response = request.get_json(force=True)
    except BadRequest:
        raise InvalidUsageError("Invalid POST request to /response",
                                status_code=400,
                                payload=request.args)

    if survey_response.get('survey_id') == 'feedback':

        bound_logger = logger.bind(survey=survey_response.get("survey_type"),
                                   survey_id=survey_response.get("survey_id"))

        try:
            save_feedback_response(bound_logger, survey_response)
        except SQLAlchemyError:
            return server_error("Database error")
        except IntegrityError:
            return server_error("Integrity error")

    else:

        try:
            metadata = survey_response['metadata']
        except KeyError:
            raise InvalidUsageError("Missing metadata. Unable to save response", 400)

        bound_logger = logger.bind(user_id=metadata.get('user_id'),
                                   ru_ref=metadata.get('ru_ref'),
                                   tx_id=survey_response.get('tx_id'))

        publisher.logger = bound_logger

        try:
            invalid = save_response(bound_logger, survey_response)
        except SQLAlchemyError:
            return server_error("Database error")
        except IntegrityError:
            return server_error("Integrity error")

        if invalid:
            return jsonify(invalid)

        tx_id = survey_response.get('tx_id')

        try:

            if survey_response['survey_id'] == 'census':
                bound_logger.info("About to publish notification to ctp queue")
                queued = publisher.ctp.publish_message(tx_id)
            elif survey_response['survey_id'] == '144':
                bound_logger.info("About to publish notification to cora queue")
                queued = publisher.cora.publish_message(tx_id)
            else:
                bound_logger.info("About to publish notification to cs queue")
                queued = publisher.cs.publish_message(tx_id)

        except KeyError:
            raise InvalidUsageError("Missing survey_id. Unable to save response", 400)

        if not queued:
            return server_error("Unable to queue notification")

        bound_logger.info("Notification published successfully")
    publisher.logger = logger
    return jsonify(result="ok")


@app.route('/invalid-responses', methods=['GET'])
def do_get_invalid_responses():
    responses = get_responses(invalid=True)

    if responses:
        jsonify(responses)
    else:
        return jsonify({}), 404


@app.route('/responses', methods=['GET'])
def do_get_responses():
    page = get_responses(invalid=False)

    try:
        return jsonify([item.to_dict() for item in page.items])
    except AttributeError as e:
        logger.error("No items in page", error=e)
        return jsonify({}), 404


@app.route('/responses/<tx_id>', methods=['GET'])
def do_get_response(tx_id):
    result = get_responses(tx_id=tx_id)
    if result:
        try:
            r = object_as_dict(result.items[0])['data']
            return jsonify(r)
        except IndexError as e:
            logger.error('Empty items list in result.', error=e)
            return jsonify({}), 404
    else:
        return jsonify({}), 404


@app.route('/queue', methods=['POST'])
def do_queue():
    tx_id = request.get_json(force=True)['id']
    # check document exists with id
    result = do_get_response(tx_id)
    if result.status_code != 200:
        return result

    response = json.loads(result.response[0].decode('utf-8'))

    bound_logger = logger.bind(tx_id=tx_id)
    publisher.logger = bound_logger

    if response['survey_response']['survey_id'] == 'census':
        bound_logger.info("About to publish response to ctp queue")
        queued = publisher.ctp.publish_message(tx_id)
    elif response['survey_response']['survey_id'] == '144':
        bound_logger.info("About to publish response to cora queue")
        queued = publisher.cora.publish_message(tx_id)
    else:
        bound_logger.info("About to publish response to cs queue")
        queued = publisher.cs.publish_message(tx_id)

    if not queued:
        return server_error("Unable to queue response")

    bound_logger.info("Response published successfully")
    publisher.logger = logger
    return jsonify(result="ok")


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    try:
        logger.info("Checking database connection")
        conn = db.engine.connect()
        test_sql(conn)
    except SQLAlchemyError:
        logger.error("Failed to connect to database")
        return server_error(500)
    else:
        return jsonify({'status': 'OK'})


if __name__ == '__main__':
    # Startup
    logger.info("Starting server", version=__version__)
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
