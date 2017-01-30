import unittest
import server
from tests.test_data import test_message, updated_message
import mock
import mongomock
import json
import logging
from structlog import wrap_logger


class TestStoreService(unittest.TestCase):
    endpoint = "/responses"
    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    def add_test_data(self, db):
        docs = [{'survey_response': self.test_json}, {'survey_response': self.updated_json}]
        db.insert_many(docs)

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True

    def test_save_response_adds_doc_and_returns_id(self):
        mock_db = mongomock.MongoClient().db.collection
        logger = wrap_logger(logging.getLogger("TEST"))
        with mock.patch('server.get_db_responses', return_value=mock_db):
            mongo_id, invalid_flag = server.save_response(logger, json.loads(test_message))
            self.assertEqual(1, mock_db.count())
            self.assertIsNotNone(mongo_id)

    def test_queue_fails_returns_500(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            with mock.patch('server.queue_cs_notification', return_value=False):
                r = self.app.post(self.endpoint, data=test_message)
                self.assertEqual(500, r.status_code)

    def test_queue_succeeds_returns_200(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            with mock.patch('server.queue_cs_notification', return_value=True):
                r = self.app.post(self.endpoint, data=test_message)
                self.assertEqual(200, r.status_code)

    # /responses/<mongo_id> GET
    def test_get_invalid_id_returns_400(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '/x')
            self.assertEqual(400, r.status_code)

    def test_get_valid_id_no_doc_returns_404(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '/123456789012345678901234')
            self.assertEqual(404, r.status_code)

    def test_get_valid_id_returns_id_and_200(self):
        mock_db = mongomock.MongoClient().db.collection
        doc = {'survey_response': test_message}
        result = mock_db.insert_one(doc)
        expected_id = str(result.inserted_id)

        with mock.patch('server.get_db_responses', return_value=mock_db):
            r = self.app.get(self.endpoint + '/' + expected_id)
            self.assertIsNotNone(r.data)
            self.assertEqual(200, r.status_code)

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