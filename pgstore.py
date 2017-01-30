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
    def pool(self, *args, **kwargs):
        return ThreadedConnectionPool(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        self.pidLastSeen = os.getpid()
        self.args = args
        self.kwargs = kwargs
        self._pool = None

    def getconn(self):
        pidNow = os.getpid()
        if self._pool is None or pidNow != self.pidLastSeen:
            self._pool = self.pool(*self.args, **self.kwargs)
            self.pidLastSeen = pidNow
        return self._pool.getconn()

    def putconn(self, conn):
        return self._pool.putconn(conn)
