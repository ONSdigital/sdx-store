import hashlib
import json
import logging
import unittest

import mock
from structlog import wrap_logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import testing.postgresql

from tests.test_data import invalid_message, test_message, second_test_message, missing_tx_id_message
from tests.test_data import test_feedback_message, invalid_feedback_message

import server
from server import db, InvalidUsageError, logger


@testing.postgresql.skipIfNotInstalled
class TestStoreService(unittest.TestCase):
    endpoints = {
        'responses': '/responses',
        'invalid': '/invalid_responses',
        'queue': '/queue',
        'healthcheck': '/healthcheck'
    }

    logger = wrap_logger(logging.getLogger("TEST"))

    test_message_json = json.loads(test_message)
    # Imitate what jsonify does in flask
    test_message_sorted = json.dumps(test_message_json,
                                     sort_keys=True,
                                     indent=2,
                                     separators=(', ', ': ')) + '\n'

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
        self.assertEqual(400, r.status_code)

    def test_response_not_saved_raises_InvalidUsageError(self):
        with self.assertRaises(InvalidUsageError):
            server.save_response(self.logger, json.loads(missing_tx_id_message))

    def test_response_invalid_true_returns_false(self):
        invalid = server.save_response(logger, json.loads(invalid_message))
        self.assertEqual(True, invalid)

    def test_feedback_response_invalid_true_returns_false(self):
        invalid = server.save_feedback_response(logger, json.loads(invalid_feedback_message))
        self.assertEqual(True, invalid)

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = SQLAlchemyError
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)

    def test_response_not_saved_returns_500_feedback(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = SQLAlchemyError
            r = self.app.post(self.endpoints['responses'], data=test_feedback_message)
            self.assertEqual(500, r.status_code)

    def test_integrity_error_returns_500(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = IntegrityError(None, None, None, None)
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)

        db.session.remove()
        db.drop_all()

    def test_integrity_error_returns_500_feedback(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = IntegrityError(None, None, None, None)
            r = self.app.post(self.endpoints['responses'], data=test_feedback_message)
            self.assertEqual(500, r.status_code)

        db.session.remove()
        db.drop_all()

    # /responses/<tx_id> GET
    def test_get_id_returns_404_if_not_stored(self):
        r = self.app.get(self.endpoints['responses'] + '/x')
        self.assertEqual(404, r.status_code)

    def test_get_valid_id_returns_id_and_200(self):
        expected_id = self.test_message_json['tx_id']
        response_size_original = len(self.test_message_sorted)
        response_hash_original = hashlib.md5(self.test_message_sorted.encode('utf-8')).hexdigest()

        self.app.post(self.endpoints['responses'],
                      data=test_message,
                      content_type='application/json')

        r = self.app.get(self.endpoints['responses'] + '/' + expected_id)

        self.assertEqual(r.data, self.test_message_sorted.encode('utf-8'))
        self.assertEqual(200, r.status_code)
        self.assertEqual(r.headers['Content-MD5'], response_hash_original)
        self.assertEqual(r.headers['Content-Length'], str(response_size_original))

        db.session.remove()
        db.drop_all()

    def test_get_responses_invalid_params(self):
        r = self.app.get(self.endpoints['responses'] + '?testing=123')
        self.assertEqual(400, r.status_code)

    def test_get_responses_valid_and_invalid_params(self):
        r = self.app.get(self.endpoints['responses'] + '?survey_id=123&testing=123')
        self.assertEqual(400, r.status_code)

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
        r = self.app.get(self.endpoints['responses'] + '?per_page=0')
        self.assertEqual(400, r.status_code)

    def test_max_range_per_page(self):
        r = self.app.get(self.endpoints['responses'] + '?per_page=101')
        self.assertEqual(400, r.status_code)

    def test_min_range_page_ok(self):
        r = self.app.get(self.endpoints['responses'] + '?page=1')
        self.assertEqual(200, r.status_code)

    def test_min_range_page_bad(self):
        r = self.app.get(self.endpoints['responses'] + '?page=0')
        self.assertEqual(400, r.status_code)

    def test_healthcheck_good(self):
        r = self.app.get(self.endpoints['healthcheck'])
        self.assertEqual(200, r.status_code)

    def test_healthcheck_bad_returns_500(self):
        with mock.patch('server.test_sql') as healthMock:
            healthMock.side_effect = SQLAlchemyError
            r = self.app.get(self.endpoints['healthcheck'])
            self.assertEqual(500, r.status_code)
