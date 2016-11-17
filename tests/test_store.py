import unittest

import pg
import server
from datetime import datetime
from tests.test_data import test_message, updated_message
import mock
import json
import psycopg2
import psycopg2.extras
import testing.postgresql


class TestStoreService(unittest.TestCase):
    endpoint = "/responses"
    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True

        self.db = testing.postgresql.Postgresql()

        # Get a map of connection parameters for the database which can be passed
        # to the functions being tested so that they connect to the correct
        # database
        self.db_conf = self.db.dsn()

        # Create a connection which can be used by our test functions to set and
        # query the state of the database
        self.db_con = pg.connect(self.db_conf)

        # Create the responses table
        with mock.patch('pg.db', self.db_con):
            pg.create_table()

    def tearDown(self):
        self.db.stop()

    def add_test_data(self):
        with mock.patch('pg.db', self.db_con):
            with self.db_con() as cursor:
                for item in [self.test_json, self.updated_json]:
                    cursor.execute(
                        pg.SQL['INSERT_DOC'], {
                            'added_date': datetime.utcnow(),
                            'survey_response': psycopg2.extras.Json(item)})

    # /responses POST
    def test_empty_post_request(self):
        with mock.patch('pg.db', self.db_con):
            r = self.app.post(self.endpoint)
            self.assertEqual(400, r.status_code)

    def test_save_response_adds_doc_and_returns_id(self):
        with mock.patch('pg.db', self.db_con):
            response_id = pg.save_response(test_message, None)

            with self.db_con() as cursor:
                cursor.execute("""SELECT COUNT(*) FROM responses""")

                row_count = cursor.fetchone()[0]

            self.assertEqual(1, row_count)
            self.assertIsNotNone(response_id)

    def test_response_not_saved_returns_500(self):
        with mock.patch('pg.db', self.db_con):
            with mock.patch('pg.save_response', return_value=None):
                r = self.app.post(self.endpoint, data=test_message)
                self.assertEqual(500, r.status_code)

    def test_queue_fails_returns_500(self):
        with mock.patch('pg.db', self.db_con):
            with mock.patch('server.queue_notification', return_value=False):
                r = self.app.post(self.endpoint, data=test_message)
                self.assertEqual(500, r.status_code)

    def test_queue_succeeds_returns_200(self):
        with mock.patch('pg.db', self.db_con):
            with mock.patch('server.queue_notification', return_value=True):
                r = self.app.post(self.endpoint, data=test_message)
                self.assertEqual(200, r.status_code)

    # /responses/<response_id> GET
    def test_get_invalid_id_returns_400(self):
        with mock.patch('pg.db', self.db_con):
            r = self.app.get(self.endpoint + '/x')
            self.assertEqual(400, r.status_code)

    def test_get_valid_id_no_doc_returns_404(self):
        with mock.patch('pg.db', self.db_con):
            r = self.app.get(self.endpoint + '/123456789012345678901234')
            self.assertEqual(404, r.status_code)

    def test_get_valid_id_returns_id_and_200(self):
        with mock.patch('pg.db', self.db_con):
            with self.db_con() as cursor:
                cursor.execute(
                    pg.SQL['INSERT_DOC'], {
                        'added_date': datetime.utcnow(),
                        'survey_response': psycopg2.extras.Json(test_message)})
                expected_id = str(cursor.fetchone()[0])

        with mock.patch('pg.db', self.db_con):
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
        with mock.patch('pg.db', self.db_con):
            r = self.app.get(self.endpoint + '?survey_id=123456')
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(0, total_count)

    def test_get_responses_per_page(self):
        self.add_test_data()
        search_criteria = server.get_search_criteria(1, 1)
        search_criteria['query'].update({'json': False, 'path': 'id', 'operator': 'gt'})

        with mock.patch('pg.db', self.db_con):
            with mock.patch('server.get_search_criteria', return_value=search_criteria):
                r = self.app.get(self.endpoint + '?per_page=1')
                page_count = len(json.loads(r.data.decode('utf8'))['results'])
                total_count = json.loads(r.data.decode('utf8'))['total_hits']

                self.assertEqual(page_count, 1)
                self.assertGreaterEqual(total_count, page_count)

    def test_get_responses_survey_id(self):
        self.add_test_data()
        with mock.patch('pg.db', self.db_con):
            r = self.app.get(self.endpoint + '?survey_id=' + self.test_json['survey_id'])
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(total_count, 1)

    def test_get_responses_period(self):
        self.add_test_data()
        with mock.patch('pg.db', self.db_con):
            r = self.app.get(self.endpoint + '?period=' + self.test_json['collection']['period'])
            total_count = json.loads(r.data.decode('utf8'))['total_hits']
            self.assertEqual(total_count, 1)

    def test_get_responses_ru_ref(self):
        self.add_test_data()
        with mock.patch('pg.db', self.db_con):
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
