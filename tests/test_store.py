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

    def test_save_response_returns_id(self):
        mock_return = mongomock.MongoClient().db.collection
        with mock.patch('server.get_db_responses', return_value=mock_return):
            mongo_id = server.save_response(test_message, None)
            self.assertIsNotNone(mongo_id)

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.save_response', return_value=None):
            r = self.app.post(self.endpoint, data=test_message)
            self.assertEqual(500, r.status_code)
