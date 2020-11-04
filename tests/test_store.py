import hashlib
import json
import logging
import unittest

import mock
from structlog import wrap_logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import testing.postgresql

import settings
from tests.test_data import invalid_message, test_message, second_test_message, missing_tx_id_message
from tests.test_data import test_feedback_message, invalid_feedback_message, feedback_id_tag

import server
from server import db, InvalidUsageError, logger


@testing.postgresql.skipIfNotInstalled
class TestStoreService(unittest.TestCase):
    """There are a number of tests of failure states that have a commented out assertEquals in them with
    different longer assertion then what isn't commented out.  The reason for this is that the return value
    changes depending on what python version is being used (No I don't know why...).

    In python 3.6.3 it returns the param name as a key, and the value is a list.  In python 3.6.7+ and 3.7+
    the key is the same, but the value is a single value instead of a list.  Because we want to test both 3.6 and
    3.7 in travis, we've opted to test the common values between them until we upgrade the python version so we
    can test the whole response.

    The aim of leaving the tests commented out is so after the version is upgraded to 3.6.7+, they should be uncommented
    the weaker test above it removed and everything should just work.
    """
    endpoints = {
        'responses': '/responses',
        'invalid': '/invalid-responses',
        'queue': '/queue',
        'healthcheck': '/healthcheck',
        'old': '/responses/old',
        'feedback': '/feedback'
    }

    logger = wrap_logger(logging.getLogger("TEST"))

    test_message_json = json.loads(test_message)
    # Imitate what jsonify does in flask
    test_message_sorted = json.dumps(test_message_json,
                                     sort_keys=True,
                                     separators=(',', ':')) + '\n'

    feedback_id_tag_json = json.loads(feedback_id_tag)
    # Imitate what jsonify does in flask
    feedback_id_tag_sorted = json.dumps(feedback_id_tag_json,
                                     sort_keys=True,
                                     separators=(',', ':')) + '\n'

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        server.create_tables()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # /responses POST
    def test_empty_post_request(self):
        r = self.app.post(self.endpoints['responses'])
        self.assertEqual(r.status_code, 400)

    def test_response_not_saved_raises_InvalidUsageError(self):
        with self.assertRaises(InvalidUsageError):
            server.save_response(self.logger, json.loads(missing_tx_id_message))

    def test_response_invalid_true_returns_false(self):
        invalid = server.save_response(logger, json.loads(invalid_message))
        self.assertTrue(invalid)

    def test_feedback_response_invalid_true_returns_false(self):
        invalid = server.save_feedback_response(logger, json.loads(invalid_feedback_message))
        self.assertTrue(invalid)

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = SQLAlchemyError
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(r.status_code, 500)

    def test_response_not_saved_returns_500_feedback(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = SQLAlchemyError
            r = self.app.post(self.endpoints['responses'], data=test_feedback_message)
            self.assertEqual(r.status_code, 500)

    def test_integrity_error_returns_500(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = IntegrityError(None, None, None, None)
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(r.status_code, 500)

        db.session.remove()
        db.drop_all()

    def test_integrity_error_returns_500_feedback(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = IntegrityError(None, None, None, None)
            r = self.app.post(self.endpoints['responses'], data=test_feedback_message)
            self.assertEqual(r.status_code, 500)

        db.session.remove()
        db.drop_all()

    # /invalid-responses GET
    def test_get_invalid_responses_returns_200(self):
        r = self.app.get(self.endpoints['invalid'])
        assert r.status_code == 200

    # /responses POST
    def test_post_invalid_response(self):
        r = self.app.post(self.endpoints['responses'],
                          data=invalid_message,
                          content_type='application/json')
        assert r.status_code == 200
        assert r.data == b'true\n'

    # /feedback/<feedback_id> GET
    def test_get_feedback_ID_400_if_not_a_valid_INT(self):
        """Endpoint should return 400 if the feedback_ID is not a valid int"""
        r = self.app.get(self.endpoints['feedback'] + '/123s')
        assert r.status_code == 400
        s = self.feedback_id_tag_json['is_feedback']
        print(s)

    def test_get_feedback_ID_404_if_ID_not_stored(self):
        """Endpoint should return 404 if the feedback_ID is not stored"""
        r = self.app.get(self.endpoints['feedback'] + '/123')
        assert r.status_code == 404

    # /responses/<tx_id> GET
    def test_get_id_returns_400_if_not_a_valid_uuid(self):
        """Endpoint should return 400 if the tx_id isn't a valid uuid formatted uuid"""
        r = self.app.get(self.endpoints['responses'] + '/123')
        assert r.status_code == 400

        r = self.app.get(self.endpoints['responses'] + '/ed7d29ed-612b-e981-d5ed-0e2e3c9951e3\n')
        assert r.status_code == 400

    def test_get_id_returns_404_if_not_stored(self):
        """Endpoint should return 404 if the tx_id isn't found in the database"""
        r = self.app.get(self.endpoints['responses'] + '/35e5062b-7041-4030-8ff5-122b3ef216a9')
        assert r.status_code == 404

    def test_get_valid_id_returns_id_and_200(self):
        expected_id = self.test_message_json['tx_id']
        response_size_original = len(self.test_message_sorted)
        response_hash_original = hashlib.md5(self.test_message_sorted.encode('utf-8')).hexdigest()

        self.app.post(self.endpoints['responses'],
                      data=test_message,
                      content_type='application/json')

        r = self.app.get(self.endpoints['responses'] + '/' + expected_id)

        self.assertEqual(r.data, self.test_message_sorted.encode('utf-8'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers['Content-MD5'], response_hash_original)
        self.assertEqual(r.headers['Content-Length'], str(response_size_original))

        db.session.remove()
        db.drop_all()

    def test_get_responses_invalid_params(self):
        """Endpoint should return 400 if given an invalid parameter"""
        r = self.app.get(self.endpoints['responses'] + '?testing=123')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json['message'], 'Request args failed schema validation')
        # self.assertEqual(r.json, {'message': 'Request args failed schema validation', 'testing': '123'})

    def test_get_responses_valid_and_invalid_params(self):
        """Endpiont should return 400 if given an invalid parameter, even if there are valid ones present"""
        r = self.app.get(self.endpoints['responses'] + '?survey_id=123&testing=123')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json['message'], 'Request args failed schema validation')
        # self.assertEqual(r.json, {'message': 'Request args failed schema validation', 'survey_id': '123', 'testing': '123'})

    def test_get_responses_per_page(self):
        self.app.post(self.endpoints['responses'],
                      data=second_test_message,
                      content_type='application/json')

        self.app.post(self.endpoints['responses'],
                      data=test_message,
                      content_type='application/json')

        r = self.app.get(self.endpoints['responses'] + '?per_page=1')
        page_count = len(json.loads(r.data.decode('utf8')))
        total_count = json.loads(r.data.decode('utf8'))
        self.assertEqual(page_count, 1)
        self.assertGreaterEqual(len(total_count), page_count)

        db.session.remove()
        db.drop_all()

    # test ranges for params
    def test_min_range_per_page(self):
        """Endpoint should return 400 if a parameter fails schema validation, in this case
        being below the minimum value for 'per_page'
        """
        r = self.app.get(self.endpoints['responses'] + '?per_page=0')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json['message'], 'Request args failed schema validation')
        # self.assertEqual(r.json, {'message': 'Request args failed schema validation', 'per_page': '0'})

    def test_max_range_per_page(self):
        """Endpoint should return 400 if a parameter fails schema validation, in this case
        being below the maximumvalue for 'per_page'
        """
        r = self.app.get(self.endpoints['responses'] + '?per_page=101')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json['message'], 'Request args failed schema validation')
        # self.assertEqual(r.json, {'message': 'Request args failed schema validation', 'per_page': '101'})

    def test_min_range_page_ok(self):
        """Endpoint should return 200 if parameters pass schema validation"""
        r = self.app.get(self.endpoints['responses'] + '?page=1')
        self.assertEqual(r.status_code, 200)

    def test_min_range_page_bad(self):
        """Endpoint should return 400 if a parameter fails schema validation, in this case
        being below the minimum value for 'page'
        """
        r = self.app.get(self.endpoints['responses'] + '?page=0')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json['message'], 'Request args failed schema validation')
        # self.assertEqual(r.json, {'message': 'Request args failed schema validation', 'page': '0'})

    def test_healthcheck_good(self):
        """Healthcheck endpoint should return 200"""
        r = self.app.get(self.endpoints['healthcheck'])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, {'status': 'OK'})

    def test_healthcheck_bad_returns_500(self):
        """Healthcheck endpoint should return 500 on failure with a message as to why it's failed"""
        with mock.patch('server.test_sql') as health_mock:
            health_mock.side_effect = SQLAlchemyError
            r = self.app.get(self.endpoints['healthcheck'])
            self.assertEqual(r.status_code, 500)
            self.assertEqual(r.json, {'message': 'Failed to connect to database', 'status': 500})

    def test_delete_old_returns_204_for_no_deletes(self):
        settings.RESPONSE_RETENTION_DAYS = 90
        r = self.app.delete(self.endpoints['old'])
        self.assertEqual(r.status_code, 204)

    def test_delete_old_returns_204_when_records_deleted(self):
        with self.assertLogs(level='INFO') as cm:
            self.app.post(self.endpoints['responses'],
                          data=second_test_message,
                          content_type='application/json')

            self.app.post(self.endpoints['responses'],
                          data=test_message,
                          content_type='application/json')
            settings.RESPONSE_RETENTION_DAYS = -2  # Set retention negative so that all added records will get deleted
            r = self.app.delete(self.endpoints['old'])
            self.assertEqual(r.status_code, 204)
            self.assertIn('Old submissions deleted        count=2', cm.output[4])

    def test_delete_old_returns_500_if_not_set_in_config(self):
        settings.RESPONSE_RETENTION_DAYS = None
        r = self.app.delete(self.endpoints['old'])
        self.assertEqual(r.status_code, 500)

    def test_delete_old_does_not_delete_records_younger_than_response_retention_days(self):
        with self.assertLogs(level='INFO') as cm:
            self.app.post(self.endpoints['responses'],
                          data=second_test_message,
                          content_type='application/json')

            self.app.post(self.endpoints['responses'],
                          data=test_message,
                          content_type='application/json')
            settings.RESPONSE_RETENTION_DAYS = 1
            r = self.app.delete(self.endpoints['old'])
            self.assertEqual(r.status_code, 204)
            self.assertIn('Old submissions deleted        count=0', cm.output[4])
