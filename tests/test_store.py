import json
import logging
import unittest

import mock
from structlog import wrap_logger
import testing.postgresql
from sqlalchemy import create_engine

from tests.test_data import invalid_message, test_message, updated_message, missing_tx_id_message
import server
from server import db, InvalidUsageError, logger, SurveyResponse

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


def tearDownModule():
    # clear cached database at end of tests
    Postgresql.clear_cache()


class TestStoreService(unittest.TestCase):
    endpoints = {
        'responses': '/responses',
        'invalid': '/invalid_responses',
        'queue': '/queue',
        'healthcheck': '/queue',
    }

    logger = wrap_logger(logging.getLogger("TEST"))

    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    def setUp(self):
        self._db = Postgresql()
        db.drop_all()
        server.create_tables()
        self.app = server.app.test_client()
        self.app.testing = True

    def tearDown(self):
        self._db.stop()

    # /responses POST
    def test_empty_post_request(self):
        r = self.app.post(self.endpoints['responses'])
        self.assertEqual(400, r.status_code)

    def test_response_not_saved_raises_InvalidUsageError(self):
        with self.assertRaises(InvalidUsageError):
            server.save_response(self.logger, json.loads(missing_tx_id_message))
        db.drop_all()

    def test_response_invalid_true_returns_false(self):
        invalid = server.save_response(logger, json.loads(invalid_message))
        self.assertEqual(True, invalid)
        db.drop_all()

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.save_response', return_value=(None, False)):
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)
        db.drop_all()

    def test_queue_fails_returns_500(self):
        with mock.patch('server.queue_cs_notification', return_value=False):
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)
        db.drop_all()

    def test_queue_succeeds_returns_200(self):
        with mock.patch('server.queue_cs_notification', return_value=True):
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(200, r.status_code)
        db.drop_all()

    # /responses/<tx_id> GET
    def test_get_id_returns_404_if_not_stored(self):
        r = self.app.get(self.endpoints['responses'] + '/x')
        self.assertEqual(404, r.status_code)

    def test_get_valid_id_returns_id_and_200(self):
        with mock.patch('server.queue_cs_notification', return_value=True):
            test_json = json.loads(updated_message)
            expected_id = test_json['tx_id']

            data = SurveyResponse(tx_id=expected_id,
                                  invalid=False,
                                  data=updated_message)

            self.app.post(self.endpoints['responses'],
                          data=updated_message,
                          content_type='application/json')

            r = self.app.get(self.endpoints['responses'] + '/' + expected_id)

            self.assertIsNotNone(r.data)
            self.assertEqual(200, r.status_code)
            db.drop_all()

    # /responses?args GET
    def test_get_responses_invalid_params(self):
        r = self.app.get(self.endpoints['responses'] + '?testing=123')
        self.assertEqual(400, r.status_code)

"""
    def test_get_responses_valid_and_invalid_params(self):
        r = self.app.get(self.endpoint + '?survey_id=123&testing=123')
        self.assertEqual(400, r.status_code)

    def test_get_responses_incorrect_value(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '?survey_id=123456')
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(0, total_count)

    def test_get_responses_per_page(self):
        mock_db = mongomock.MongoClient().db.collection
        self.add_test_data(mock_db)
        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '?per_page=1')
            page_count = len(json.loads(r.data.decode('utf8'))['results'])
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(page_count, 1)
            self.assertGreaterEqual(total_count, page_count)

    def test_get_responses_survey_id(self):
        mock_db = mongomock.MongoClient().db.collection
        self.add_test_data(mock_db)
        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '?survey_id=' + self.test_json['survey_id'])
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(total_count, 1)

    def test_get_responses_period(self):
        mock_db = mongomock.MongoClient().db.collection
        self.add_test_data(mock_db)
        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '?period=' + self.test_json['collection']['period'])
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(total_count, 1)

    def test_get_responses_ru_ref(self):
        mock_db = mongomock.MongoClient().db.collection
        self.add_test_data(mock_db)
        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '?ru_ref=' + self.test_json['metadata']['ru_ref'])
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(total_count, 1)

    # test ranges for params
    def test_min_range_per_page(self):
        r = self.app.get(self.endpoint + '?per_page=0')
        self.assertEqual(400, r.status_code)

    def test_max_range_per_page(self):
        r = self.app.get(self.endpoint + '?per_page=101')
        self.assertEqual(400, r.status_code)

    def test_min_range_page(self):
        r = self.app.get(self.endpoint + '?page=0')
        self.assertEqual(400, r.status_code)
"""
