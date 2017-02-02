import json
import unittest

import server
from tests.test_data import test_message, updated_message

import mock
import testing.postgresql


class TestStoreService(unittest.TestCase):
    endpoint = "/responses"
    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    @classmethod
    def setUpClass(cls):
        cls.pm = server.pm

    def setUp(self):
        self.db = testing.postgresql.Postgresql()
        self.pm.kwargs = self.db.dsn()
        server.create_tables()
        self.app = server.app.test_client()
        self.app.testing = True

    def tearDown(self):
        self.pm.closeall()
        self.db.stop()

    # /responses POST
    def test_empty_post_request(self):
        r = self.app.post(self.endpoint)
        self.assertEqual(400, r.status_code)

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.save_response', return_value=(None, False)):
            r = self.app.post(self.endpoint, data=test_message)
            self.assertEqual(500, r.status_code)

    # /responses?args GET
    def test_get_responses_invalid_params(self):
        r = self.app.get(self.endpoint + '?testing=123')
        self.assertEqual(400, r.status_code)

    def test_get_responses_valid_and_invalid_params(self):
        r = self.app.get(self.endpoint + '?survey_id=123&testing=123')
        self.assertEqual(400, r.status_code)

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
