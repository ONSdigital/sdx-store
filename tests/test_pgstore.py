import unittest

from pgstore import ProcessSafePoolManager


class PoolManagerTests(unittest.TestCase:

    def setUp(self):
        self.pm = ProcessSafePoolManager(1, 10, "host='127.0.0.1' port=12099")

    def test_connect(self):
        self.fail()
