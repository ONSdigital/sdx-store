from collections import OrderedDict
import datetime
import os
import unittest

import psycopg2.extensions
import psycopg2.pool
import testing.postgresql

from pgstore import ResponseStore
from pgstore import ProcessSafePoolManager


@testing.postgresql.skipIfNotInstalled
class SQLTests(unittest.TestCase):
    factory = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)

    def setUp(self):
        self.db = self.factory()

    def tearDown(self):
        self.db.stop()

    @classmethod
    def tearDownClass(cls):
        cls.factory.clear_cache()

    def test_create(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        try:
            con = pm.getconn()
            ResponseStore.Creation().run(con)

            cur = con.cursor()
            cur.execute("select * from pg_catalog.pg_tables")
            check = schema, name, owner, space, hasIndexes, hasRules, hasTriggers, rowSec = (
                "public", "responses", "postgres", None, True, False, False, False
            )
            self.assertIn(check, cur.fetchall())

        finally:
            pm.putconn(con)

    def test_insert_response(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        try:
            con = pm.getconn()
            ResponseStore.Creation().run(con)
            ResponseStore.Insertion(
                id="9bca1e45-310b-4677-bb86-255da5c7eb34",
                data={
                    "survey_id": "144",
                    "metadata": {
                        "user_id": "sdx",
                        "ru_ref": "12346789012A"
                    },
                    "data": {}
                }
            ).run(con)

        finally:
            pm.putconn(con)

    def test_select_response(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        response = {
            "survey_id": "144",
            "metadata": {
                "user_id": "sdx",
                "ru_ref": "12346789012A"
            },
            "data": {}
        }
        try:
            con = pm.getconn()
            ResponseStore.Creation().run(con)

            then = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
            ResponseStore.Insertion(
                id="9bca1e45-310b-4677-bb86-255da5c7eb34",
                data=response
            ).run(con)

            rv = ResponseStore.Selection(
                id="9bca1e45-310b-4677-bb86-255da5c7eb34"
            ).run(con)
            now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
            self.assertIsInstance(rv, OrderedDict)
            self.assertIsNone(rv["valid"])
            self.assertEqual(response, rv["data"], rv)
            self.assertIsInstance(rv["ts"], datetime.datetime)
            self.assertTrue(then < rv["ts"] < now)

        finally:
            pm.putconn(con)

    def test_list_responses(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        response = {
            "survey_id": "144",
            "metadata": {
                "user_id": "sdx",
                "ru_ref": "12346789012A"
            },
            "data": {}
        }
        try:
            con = pm.getconn()
            ResponseStore.Creation().run(con)

            then = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
            ResponseStore.Insertion(
                id="9bca1e45-310b-4677-bb86-255da5c7eb34",
                valid=True,
                data=response
            ).run(con)

            rv = ResponseStore.Filter(valid=True).run(con)
            now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
            self.assertIsInstance(rv, list)
            self.assertEqual(1, len(rv))
            self.assertIs(True, rv[0]["valid"])
            self.assertEqual(response, rv[0]["data"])
            self.assertIsInstance(rv[0]["ts"], datetime.datetime)
            self.assertTrue(then < rv[0]["ts"] < now)

            rv = ResponseStore.Filter(valid=False).run(con)
            self.assertIsInstance(rv, list)
            self.assertEqual(0, len(rv))
        finally:
            pm.putconn(con)


@testing.postgresql.skipIfNotInstalled
class PoolManagerTests(unittest.TestCase):

    def setUp(self):
        self.db = testing.postgresql.Postgresql()

    def tearDown(self):
        self.db.stop()

    def test_first_connect(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        self.assertIsNone(pm._pool)

        con = pm.getconn()
        self.assertIsInstance(pm._pool, psycopg2.pool.ThreadedConnectionPool)
        self.assertEqual(1, len(pm._pool._used))
        self.assertIsInstance(con, psycopg2.extensions.connection)

        pm.putconn(con)
        self.assertEqual(0, len(pm._pool._used))

    def test_connect_after_fork(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        self.assertEqual(os.getpid(), pm.pidLastSeen)

        pm.getconn()
        pools = [pm._pool]

        pm.pidLastSeen -= 1
        pm.getconn()
        pools.append(pm._pool)

        self.assertIsNot(pools[0], pools[1])
