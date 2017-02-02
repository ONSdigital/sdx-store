from collections import OrderedDict
import os
import re
import textwrap

import psycopg2
from psycopg2.extras import Json
from psycopg2.pool import ThreadedConnectionPool


def get_dsn(settings=None):
    rv = {
        k: getattr(settings, v)
        for k, v in (
            ("host", "DB_HOST"), ("port", "DB_PORT"),
            ("dbname", "DB_NAME"), ("user", "DB_USER"), ("password", "DB_PASSWORD")
        )
    }
    return rv


class ResponseStore:

    idPattern = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    class SQLOperation:
        cols = ("id", "ts", "valid", "data")

        @staticmethod
        def sql():
            raise NotImplementedError

        def __init__(self, **kwargs):
            self.params = {c: kwargs.get(c) for c in self.cols}

        def run(self, con, log=None):
            """
            Execute the SQL defined by this class.
            Returns the cursor for data extraction.

            """
            cur = con.cursor()
            cur.execute(self.sql(), self.params)
            con.commit()
            return cur

    class Creation(SQLOperation):

        @staticmethod
        def sql():
            return textwrap.dedent("""
            CREATE TABLE IF NOT EXISTS responses (
              id uuid PRIMARY KEY,
              ts timestamp WITH time zone DEFAULT NOW(),
              valid boolean DEFAULT NULL,
              data jsonb
            )""")

        def run(self, con, log=None):
            cur = super().run(con)
            cur.close()

    class Insertion(SQLOperation):

        @staticmethod
        def sql(**kwargs):
            return textwrap.dedent("""
            INSERT INTO responses (id, valid, data)
              VALUES (%(id)s, %(valid)s, %(data)s)
              RETURNING id
            """)

        def __init__(self, **kwargs):
            kwargs["data"] = Json(kwargs.get("data", "{}"))
            super().__init__(**kwargs)

        def run(self, con, log=None):
            cur = super().run(con)
            rv = cur.fetchone()
            cur.close()
            return rv[0] if rv else None

    class Selection(SQLOperation):

        @staticmethod
        def sql(**kwargs):
            return textwrap.dedent("""
            SELECT id, ts, valid, data FROM responses
              WHERE id = %(id)s
            """)

        def run(self, con, log=None):
            cur = super().run(con)
            rv = {}
            try:
                row = cur.fetchone()
            except psycopg2.ProgrammingError:
                pass  # Default return value
            else:
                rv = OrderedDict(
                    (k, v) for k, v in zip(self.cols, row)
                )
            finally:
                cur.close()
                return rv

    class Filter(SQLOperation):

        @staticmethod
        def sql(**kwargs):
            return textwrap.dedent("""
            SELECT id, ts, valid, data FROM responses
              WHERE valid = %(valid)s
            """)

        def run(self, con, log=None):
            cur = super().run(con)
            rv = [
                OrderedDict((k, v) for k, v in zip(self.cols, row))
                for row in cur.fetchall()
            ]
            cur.close()
            return rv


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
        if self._pool is None or self._pool.closed or pidNow != self.pidLastSeen:
            minconn = self.kwargs.pop("minconn", 1)
            maxconn = self.kwargs.pop("maxconn", 16)
            self._pool = self.pool(minconn, maxconn, **self.kwargs)
            self.pidLastSeen = pidNow
        return self._pool.getconn()

    def putconn(self, conn):
        return self._pool.putconn(conn)

    def closeall(self):
        return self._pool.closeall()
