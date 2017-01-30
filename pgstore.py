import os
from psycopg2.pool import ThreadedConnectionPool


class ProcessSafePoolManager:
    """
    Connection pooling presents a challenge when gunicorn forks a worker
    after the pool is created. The result can be two worker processes claiming
    the same connection from the pool.

    See https://gist.github.com/jeorgen/4eea9b9211bafeb18ada for the basis of
    this solution.

    """

    @staticmethod
    def pool(*args, **kwargs):
        return ThreadedConnectionPool(*args, **kwargs)

    def __init__(self, **kwargs):
        self.pidLastSeen = os.getpid()
        self.kwargs = kwargs
        self._pool = None

    def getconn(self):
        pidNow = os.getpid()
        if self._pool is None or pidNow != self.pidLastSeen:
            minconn = self.kwargs.pop("minconn", 1)
            maxconn = self.kwargs.pop("maxconn", 16)
            self._pool = self.pool(minconn, maxconn, **self.kwargs)
            self.pidLastSeen = pidNow
        return self._pool.getconn()

    def putconn(self, conn):
        return self._pool.putconn(conn)
