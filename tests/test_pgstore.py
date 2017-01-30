import unittest

import testing.postgresql

from pgstore import ProcessSafePoolManager


@testing.postgresql.skipIfNotInstalled
class PoolManagerTests(unittest.TestCase):

    def setUp(self):
        self.db = testing.postgresql.Postgresql()

    def tearDown(self):
        self.db.stop()

    def test_connect(self):
        pm = ProcessSafePoolManager(**self.db.dsn())
        self.assertIsNone(pm._pool)
