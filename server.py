import datetime
import hashlib
import os
import uuid

from flask import jsonify, request
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DataError
from voluptuous import All, Coerce, MultipleInvalid, Range, Schema
from werkzeug.exceptions import BadRequest

from app.exceptions import InvalidUsageError
from app.models import FeedbackResponse, SurveyResponse
from app import app, db, logger
import settings

schema = Schema({
    'added_ms': Coerce(int),
    'form': str,
    'page': All(Coerce(int), Range(min=1)),
    'period': str,
    'per_page': All(Coerce(int), Range(min=1, max=100)),
    'ru_ref': str,
    'survey_id': str,
})


def create_tables():
    logger.info("Creating tables")
    db.create_all()


if os.getenv("CREATE_TABLES", False):
    create_tables()


def get_responses(tx_id=None, invalid=None):
    try:
        schema(request.args.to_dict())
    except MultipleInvalid:
        raise InvalidUsageError("Request args failed schema validation", payload=request.args)

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


# pylint: disable=maybe-no-member
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
    """Converts a sqlalchemy object into a dictionary where the column names are the keys"""
    return {column.key: getattr(obj, column.key)
            for column in inspect(obj).mapper.column_attrs}


def save_response(bound_logger, survey_response):
    bound_logger.info("Saving response")

    invalid = survey_response.get("invalid")
    if invalid:
        bound_logger.info("Invalid key found in response. Popping invalid key before saving")
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
        db.session.flush()
        new_id = feedback_response.id
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

    return invalid, new_id


def test_sql(connection):
    """Run a SELECT 1 to test the database connection"""
    logger.debug("Executing select 1")
    connection.scalar(select([1]))


@app.errorhandler(500)
def server_error(error):
    """Handles the building and returning of a response in the case of an error"""
    logger.error(error, status=500)
    message = {
        'status': 500,
        'message': error,
    }

    resp = jsonify(message)
    resp.status_code = 500
    return resp


@app.errorhandler(InvalidUsageError)
def invalid_usage_error(error):
    logger.error(error.message, status_code=error.status_code, payload=error.payload, url=request.url)
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

    result = {'tx_id': survey_response.get('tx_id'),
              'is_feedback': False}

    if response_type.find("feedback") != -1:
        bound_logger = bound_logger.bind(response_type="feedback",
                                         survey_id=survey_response.get("survey_id"))
        try:
            feedback = save_feedback_response(bound_logger, survey_response)
            result['is_feedback'] = True
            result['feedback_id'] = feedback[1]
        except IntegrityError:
            return server_error("Integrity error")
        except SQLAlchemyError:
            return server_error("Database error")
    else:
        try:
            metadata = survey_response['metadata']
        except KeyError:
            raise InvalidUsageError("Missing metadata. Unable to save response", 400)

        bound_logger = bound_logger.bind(user_id=metadata.get('user_id'),
                                         ru_ref=metadata.get('ru_ref'))

        try:
            invalid = save_response(bound_logger, survey_response)

        except IntegrityError:
            return server_error("Integrity error")
        except DataError:
            raise InvalidUsageError("Invalid characters in payload", 400, payload={'contains_invalid_character': True})
        except SQLAlchemyError:
            return server_error("Database error")

        if invalid:
            return jsonify(invalid)

    return jsonify(result)


@app.route('/invalid-responses', methods=['GET'])
def do_get_invalid_responses():
    """Returns every invalid response in the database"""
    page = get_responses(invalid=True)
    return jsonify([item.to_dict() for item in page.items])


@app.route('/responses', methods=['GET'])
def do_get_responses():
    page = get_responses(invalid=False)

    try:
        return jsonify([item.to_dict() for item in page.items])
    except AttributeError:
        logger.exception("No items in page")
        return jsonify({}), 404


@app.route('/feedback_responses/<id>', methods=['GET'])
def do_get_feedback(feedback_response):
    if feedback_response.find("feedback") != -1:
        print("THIS IS FEEDBACK")


@app.route('/responses/<tx_id>', methods=['GET'])
def do_get_response(tx_id):
    try:
        uuid.UUID(tx_id, version=4)
    except ValueError:
        raise InvalidUsageError("tx_id supplied is not a valid UUID", 400)

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


@app.route('/responses/old', methods=['DELETE'])
def delete_old_responses():
    """Deletes responses that are older than the number of days set in config
    Config use is a compromise for safety in case incorrect parameters are passed.
    """
    try:
        response_retention_days = int(settings.RESPONSE_RETENTION_DAYS)

        # Get the cut off date
        time_delta = datetime.timedelta(days=response_retention_days)
        cut_off_date = datetime.datetime.utcnow() - time_delta

        # Set time element of cut off date to 0:0:0.0
        cut_off_date = cut_off_date.combine(cut_off_date.date(),
                                            datetime.time(hour=0, minute=0, second=0, microsecond=0, tzinfo=None))

        deleted_count = db.session.query(SurveyResponse).filter(SurveyResponse.ts < cut_off_date) \
            .delete(synchronize_session=False)
        db.session.commit()

        logger.info('Old submissions deleted', count=deleted_count, cut_off_date=cut_off_date.strftime('%Y-%d-%m'))

    except SQLAlchemyError:
        return server_error("Database error")
    except TypeError:  # Thrown if RESPONSE_RETENTION_DAYS is not set
        return server_error('Response retention days not configured')

    return jsonify({}), 204


@app.route('/info', methods=['GET'])
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    try:
        logger.info("Checking database connection")
        conn = db.engine.connect()
        test_sql(conn)
    except SQLAlchemyError:
        return server_error("Failed to connect to database")
    else:
        return jsonify({'status': 'OK'})


if __name__ == '__main__':
    # Startup
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
