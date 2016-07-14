import unittest
import server
from tests.test_data import test_message, updated_message
import mock
import mongomock
import json


class TestStoreService(unittest.TestCase):
    endpoint = "/responses"
    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True

    def add_test_data(self, db):
        docs = [{'survey_response': self.test_json}, {'survey_response': self.updated_json}]
        db.insert_many(docs)

    # /responses POST
    def test_empty_post_request(self):
        r = self.app.post(self.endpoint)
        self.assertEqual(400, r.status_code)

    def test_save_response_adds_doc_and_returns_id(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            mongo_id = server.save_response(test_message, None)
            self.assertEqual(1, mock_db.count())
            self.assertIsNotNone(mongo_id)

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.save_response', return_value=None):
            r = self.app.post(self.endpoint, data=test_message)
            self.assertEqual(500, r.status_code)

    def test_queue_fails_returns_500(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            with mock.patch('server.queue_notification', return_value=False):
                r = self.app.post(self.endpoint, data=test_message)
                self.assertEqual(500, r.status_code)

    def test_queue_succeeds_returns_200(self):
        mock_db = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_db):
            with mock.patch('server.queue_notification', return_value=True):
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

    # /responses?args GET
    def test_get_responses_invalid_params(self):
        r = self.app.get(self.endpoint + '?testing=123')
        self.assertEqual(400, r.status_code)

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
