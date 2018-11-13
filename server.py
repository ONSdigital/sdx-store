import hashlib
import logging
import os

from flask import jsonify, Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, select, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from structlog import wrap_logger
from voluptuous import All, Coerce, MultipleInvalid, Range, Schema
from werkzeug.exceptions import BadRequest

import settings


__version__ = "3.6.0"

logging.basicConfig(format=settings.LOGGING_FORMAT,
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    level=settings.LOGGING_LEVEL)

logger = wrap_logger(logging.getLogger(__name__))

logger.info("Starting SDX Store", version=__version__)

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


if os.getenv("CREATE_TABLES", False):
    create_tables()


def get_responses(tx_id=None, invalid=None):
    try:
        schema(request.args)
    except MultipleInvalid:
        raise InvalidUsageError("Request args failed schema validation",
                                status_code=400,
                                payload=request.args)

    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=100)

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
    '''Converts a sqlalchemy object into a dictionary where the column names are the keys'''
    return {column.key: getattr(obj, column.key)
            for column in inspect(obj).mapper.column_attrs}


def save_response(bound_logger, survey_response):
    bound_logger.info("Saving response")

    invalid = survey_response.get("invalid")
    if invalid:
        survey_response.pop("invalid")

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
    survey = survey_feedback_response.get("survey_id")
    period = survey_feedback_response.get("collection", {}).get("period")

    invalid = survey_feedback_response.get("invalid")
    if invalid:
        survey_feedback_response.pop("invalid")

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

    bound_logger = logger.bind(tx_id=survey_response.get('tx_id'))

    response_type = str(survey_response.get('type'))

    if response_type.find("feedback") != -1:
        bound_logger = bound_logger.bind(response_type="feedback",
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

        bound_logger = bound_logger.bind(user_id=metadata.get('user_id'),
                                   ru_ref=metadata.get('ru_ref'))

        try:
            invalid = save_response(bound_logger, survey_response)
        except SQLAlchemyError:
            return server_error("Database error")
        except IntegrityError:
            return server_error("Integrity error")

        if invalid:
            return jsonify(invalid)

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
    except AttributeError:
        logger.exception("No items in page")
        return jsonify({}), 404


@app.route('/responses/<tx_id>', methods=['GET'])
def do_get_response(tx_id):
    result = get_responses(tx_id=tx_id)
    if result:
        try:
            result_dict = object_as_dict(result.items[0])['data']
            response = jsonify(result_dict)
            response.headers['Content-MD5'] = hashlib.md5(response.data).hexdigest()
            return response

        except IndexError:
            logger.exception('Empty items list in result.')
            return jsonify({}), 404

    else:
        return jsonify({}), 404


@app.route('/info', methods=['GET'])
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
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
