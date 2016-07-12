import unittest
import server
from tests.test_data import test_message
import mock
import mongomock


class TestStoreService(unittest.TestCase):
    endpoint = "/responses"

    def setUp(self):
        # creates a test client
        self.app = server.app.test_client()
        # propagate the exceptions to the test client
        self.app.testing = True

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

    def test_get_responses_invalid_params(self):
        r = self.app.get(self.endpoint + '?testing=123')
        self.assertEqual(400, r.status_code)
