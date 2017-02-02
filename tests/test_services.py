import json
import logging
import unittest

import mock
from structlog import wrap_logger

import pgstore
import server
import testing.postgresql

from tests.test_data import test_message, updated_message


class TestStoreService(unittest.TestCase):
    endpoint = "/responses"
    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    def add_test_data(self):
        con = self.pm.getconn()
        try:
            for data in [json.loads(i) for i in (self.test_json, self.updated_json)]:
                ResponseStore.Insertion(id=data["tx_id"], data=data).run(con)
        finally:
            self.pm.putconn(con)

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

    def test_save_response_adds_json_and_returns_id(self):
        logger = wrap_logger(logging.getLogger("TEST"))
        data = json.loads(test_message)
        tx_id, invalid_flag = server.save_response(logger, data)
        self.assertEqual(data["tx_id"], tx_id)

    def test_queue_fails_returns_500(self):
        with mock.patch('server.queue_cs_notification', return_value=False):
            r = self.app.post(self.endpoint, data=test_message)
            self.assertEqual(500, r.status_code)

    def test_queue_succeeds_returns_200(self):
        with mock.patch('server.queue_cs_notification', return_value=True):
            r = self.app.post(self.endpoint, data=test_message)
            self.assertEqual(200, r.status_code)

    # /responses/<tx_id> GET
    def test_get_invalid_id_returns_400(self):
        r = self.app.get(self.endpoint + '/x')
        self.assertEqual(400, r.status_code)

    def test_get_valid_id_no_doc_returns_404(self):
        r = self.app.get(self.endpoint + "/f5d8bff5-ae44-46af-a567-c9040c2202c9")
        self.assertEqual(404, r.status_code)

    def test_get_valid_id_returns_id_and_200(self):
        data = json.loads(test_message)

        try:
            con = self.pm.getconn()
            pgstore.ResponseStore.Insertion(id=data["tx_id"], data=data).run(con)
        finally:
            self.pm.putconn(con)

        r = self.app.get(self.endpoint + '/' + data["tx_id"])
        self.assertIsNotNone(r.data)
        self.assertEqual(200, r.status_code)
