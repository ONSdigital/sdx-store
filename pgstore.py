import os
import textwrap

from psycopg2.extras import Json
from psycopg2.pool import ThreadedConnectionPool


class SQLOperation:

    @staticmethod
    def sql():
        raise NotImplementedError

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def run(self, con):
        """
        Execute the SQL defined by this class.
        Returns the cursor for data extraction.

        """
        cur = con.cursor()
        print(cur.mogrify(self.sql(), self.kwargs))
        cur.execute(self.sql(), self.kwargs)
        con.commit()
        return cur


class CreateResponseTable(SQLOperation):

    @staticmethod
    def sql():
        return textwrap.dedent("""
        CREATE TABLE IF NOT EXISTS responses (
          id uuid PRIMARY KEY,
          ts timestamp WITH time zone,
          data jsonb
        )""")

    def run(self, con):
        cur = super().run(con)
        cur.close()


class InsertResponse(SQLOperation):

    @staticmethod
    def sql(**kwargs):
        return textwrap.dedent("""
        INSERT INTO responses (id, data)
          VALUES (%(id)s, %(data)s)
        """)

    def __init__(self, **kwargs):
        kwargs["data"] = Json(kwargs.get("data", "{}"))
        print(kwargs)
        super().__init__(**kwargs) 

    def run(self, con):
        cur = super().run(con)
        cur.close()


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
