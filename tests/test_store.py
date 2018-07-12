import json
import logging
import mock
import unittest

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from structlog import wrap_logger
import testing.postgresql

import exporter
import server
from server import db, InvalidUsageError, logger
from tests.test_data import invalid_message, test_message, updated_message, missing_tx_id_message
from tests.test_data import test_feedback_message, invalid_feedback_message


@testing.postgresql.skipIfNotInstalled
class TestStoreService(unittest.TestCase):
    endpoints = {
        'responses': '/responses',
        'invalid': '/invalid_responses',
        'queue': '/queue',
        'healthcheck': '/healthcheck',
        'comments': '/comments',
    }

    rsi_data = {"data": {"11": "1/4/2016", "12": "31/10/2016", "20": "1800000", "21": "60000", "22": "705000", "23": "900",
                         "24": "74", "25": "50", "26": "100", "27": "7400", "50": "205", "51": "84", "52": "10", "53": "73",
                         "54": "24", "146": "Change comments included", "146a": "Yes",
                         "146b": "In-store / online promotions", "146c": "Special events (e.g. sporting events)",
                         "146d": "Calendar events (e.g. Christmas, Easter, Bank Holiday)", "146e": "Weather",
                         "146f": "Store closures", "146g": "Store openings", "146h": "Other"},
                "type": "uk.gov.ons.edc.eq:surveyresponse", "tx_id": "0d51ca67-98d9-4ae9-9187-2887f24c0a1f",
                "origin": "uk.gov.ons.edc.eq", "version": "0.0.1",
                "metadata": {"ru_ref": "12345678901A", "user_id": "789473423"},
                "survey_id": "023", "collection": {"period": "1604", "exercise_sid": "hfjdskf", "instrument_id": "0215"},
                "submitted_at": "2016-03-12T10:39:40Z"}

    logger = wrap_logger(logging.getLogger("TEST"))

    test_json = json.loads(test_message)
    updated_json = json.loads(updated_message)

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        server.create_tables()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

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

    def test_feedback_response_invalid_true_returns_false(self):
        invalid = server.save_feedback_response(logger, json.loads(invalid_feedback_message))
        self.assertEqual(True, invalid)

    def test_response_not_saved_returns_500(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = SQLAlchemyError
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)

    def test_response_not_saved_returns_500_feedback(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = SQLAlchemyError
            r = self.app.post(self.endpoints['responses'], data=test_feedback_message)
            self.assertEqual(500, r.status_code)

    def test_integrity_error_returns_500(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = IntegrityError(None, None, None, None)
            r = self.app.post(self.endpoints['responses'], data=test_message)
            self.assertEqual(500, r.status_code)

        db.session.remove()
        db.drop_all()

    def test_integrity_error_returns_500_feedback(self):
        with mock.patch('server.db.session.commit') as db_mock:
            db_mock.side_effect = IntegrityError(None, None, None, None)
            r = self.app.post(self.endpoints['responses'], data=test_feedback_message)
            self.assertEqual(500, r.status_code)

        db.session.remove()
        db.drop_all()

    # /responses/<tx_id> GET
    def test_get_id_returns_404_if_not_stored(self):
        r = self.app.get(self.endpoints['responses'] + '/x')
        self.assertEqual(404, r.status_code)

    def test_get_valid_id_returns_id_and_200(self):
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

    def test_create_workbook(self):
        comments = [server.SurveyResponse('123', True, self.rsi_data)]
        workbook, filename = exporter.create_comments_book('023', comments)
        self.assertIs(type(workbook), bytes)
        self.assertIs(type(filename), str)

    def test_get_comments(self):
        with mock.patch('server.get_all_comments_by_survey_id') as result_mock:
            result_mock.return_value = [server.SurveyResponse('123', True, self.rsi_data)]

            response = self.app.get(self.endpoints['comments'] + '/023')
            self.assertEqual(200, response.status_code)
            self.assertIs(type(response.get_data()), bytes)

    def test_get_comments_has_errors(self):
        with mock.patch('server.get_all_comments_by_survey_id') as result_mock:
            result_mock.side_effect = SQLAlchemyError

            response = self.app.get(self.endpoints['comments'] + '/023')
            self.assertEqual(500, response.status_code)
            self.assertEqual(response.get_data(), b'{\n  "message": "Database error", \n  "status": 500\n}\n')
