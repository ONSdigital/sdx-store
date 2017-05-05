import json
import logging
import os
import unittest

import mock
from structlog import wrap_logger
from sqlalchemy.exc import SQLAlchemyError
import testing.postgresql

from tests.test_data import invalid_message, test_message, updated_message, missing_tx_id_message

os.environ['SDX_STORE_POSTGRES_HOST'] = '0.0.0.0'
os.environ['SDX_STORE_POSTGRES_PORT'] = '5432'
os.environ['SDX_STORE_POSTGRES_NAME'] = 'postgres'
os.environ['SDX_STORE_POSTGRES_USER'] = 'postgres'
os.environ['SDX_STORE_POSTGRES_PASSWORD'] = 'secret'
os.environ['RABBITMQ_HOST'] = 'rabbit'
os.environ['RABBITMQ_PORT'] = '5672'
os.environ['RABBITMQ_DEFAULT_USER'] = 'rabbit'
os.environ['RABBITMQ_DEFAULT_PASS'] = 'rabbit'
os.environ['RABBITMQ_DEFAULT_VHOST'] = '2%f'
os.environ['RABBITMQ_HOST2'] = '0.0.0.0'
os.environ['RABBITMQ_PORT2'] = '5433'
os.environ['RABBIT_CORA_QUEUE'] = 'sdx-cora-survey-notifications'
os.environ['RABBIT_CTP_QUEUE'] = 'sdx-ctp-survey-notifications'
os.environ['RABBIT_CS_QUEUE'] = 'sdx-cs-survey-notifications'

import server
from server import db, InvalidUsageError, logger

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


def tearDownModule():
    # clear cached database at end of tests
    Postgresql.clear_cache()


class TestStoreService(unittest.TestCase):
    endpoints = {
        'responses': '/responses',
        'invalid': '/invalid_responses',
        'queue': '/queue',
        'healthcheck': '/healthcheck',
    }

    logger = wrap_logger(logging.getLogger("TEST"))

    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    def setUp(self):
        self.postgres = Postgresql()
        self.app = server.app.test_client()
        self.app.testing = True
        server.check_default_env_vars()
        server.create_tables()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.postgres.stop()

    def test_missing_envvar_raises_value_error(self):
        with self.assertRaises(ValueError):
            server._get_value('TEST')

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

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.save_response', return_value=(None, False)):
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)

    def test_queue_fails_returns_500(self):
        with mock.patch('server.publisher.cs.publish_message', return_value=False):
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)

        db.session.remove()
        db.drop_all()

    def test_queue_succeeds_returns_200(self):
        with mock.patch('server.publisher.cs.publish_message', return_value=True):
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(200, r.status_code)

        db.session.remove()
        db.drop_all()

    # /responses/<tx_id> GET
    def test_get_id_returns_404_if_not_stored(self):
        r = self.app.get(self.endpoints['responses'] + '/x')
        self.assertEqual(404, r.status_code)

    def test_get_valid_id_returns_id_and_200(self):
        with mock.patch('server.publisher.cs.publish_message', return_value=True):
            test_json = json.loads(updated_message)
            expected_id = test_json['tx_id']

            self.app.post(self.endpoints['responses'],
                          data=updated_message,
                          content_type='application/json')

            r = self.app.get(self.endpoints['responses'] + '/' + expected_id)

            self.assertIsNotNone(r.data)
            self.assertEqual(200, r.status_code)

        db.session.remove()
        db.drop_all()

    def test_get_responses_invalid_params(self):
        r = self.app.get(self.endpoints['responses'] + '?testing=123')
        self.assertEqual(400, r.status_code)

    def test_get_responses_valid_and_invalid_params(self):
        r = self.app.get(self.endpoints['responses'] + '?survey_id=123&testing=123')
        self.assertEqual(400, r.status_code)

    def test_get_responses_per_page(self):
        with mock.patch('server.publisher.cs.publish_message', return_value=True):
            self.app.post(self.endpoints['responses'],
                          data=updated_message,
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
