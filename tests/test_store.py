import unittest
from server import app


class TestStoreService(unittest.TestCase):

    endpoint = "/responses"

    def setUp(self):
        # creates a test client
        self.app = app.test_client()
        # propagate the exceptions to the test client
        self.app.testing = True

    def test_empty_post_request(self):
        r = self.app.post(self.endpoint)
        self.assertEqual(400, r.status_code)

    def test_run(self):
        self.assertEqual(True, True)
