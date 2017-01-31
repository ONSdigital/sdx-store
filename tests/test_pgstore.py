import os
import unittest

import psycopg2.extensions
import psycopg2.pool
import testing.postgresql

from pgstore import CreateResponseTable
from pgstore import ProcessSafePoolManager

"""
"tx_id": "9bca1e45-310b-4677-bb86-255da5c7eb34",
"""


@testing.postgresql.skipIfNotInstalled
class SQLTests(unittest.TestCase):
    factory = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)

    def test_create(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        try:
            con = pm.getconn()
            CreateResponseTable().run(con)

            cur = con.cursor()
            cur.execute("select * from pg_catalog.pg_tables")
            check = schema, name, owner, space, hasIndexes, hasRules, hasTriggers, rowSec = (
                "public", "responses", "postgres", None, True, False, False, False
            )
            self.assertIn(check, cur.fetchall())

        finally:
            pm.putconn(con)

    def setUp(self):
        self.db = self.factory()

    def tearDown(self):
        self.db.stop()

    @classmethod
    def tearDownClass(cls):
        cls.factory.clear_cache()


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
