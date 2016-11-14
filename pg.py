from datetime import datetime

import psycopg2
import psycopg2.extras

from server import app


SQL = {
    "INSERT_DOC": """
        INSERT INTO responses(
            added_date,
            survey_response)
        VALUES (
            %(added_date)s,
            %(survey_response)s)
        RETURNING id
    """,

    "SELECT_EQ_ID": """
        SELECT * FROM responses
        WHERE id = %s
    """,

    "SELECT_GT_ID": """
        SELECT * FROM responses
        WHERE id > %s
    """,

    "COUNT_GT_ID": """
        SELECT COUNT(*) FROM responses
        WHERE id > %s
    """,

    "SELECT_GTE_ADDED_DATE": """
        SELECT * FROM responses
        WHERE added_date >= %s
    """,

    "COUNT_GTE_ADDED_DATE": """
        SELECT * FROM responses
        WHERE added_date >= %s
    """,

    "SELECT_FIRST_LEVEL": """
        SELECT * FROM responses
        WHERE survey_response ->> %s = %s
    """,

    "SELECT_SECOND_LEVEL": """
        SELECT * FROM responses
        WHERE survey_response #> %s = %s
    """,

    "COUNT_FIRST_LEVEL": """
        SELECT COUNT(*) FROM responses
        WHERE survey_response ->> %s = %s
    """,

    "COUNT_SECOND_LEVEL": """
        SELECT COUNT(*) FROM responses
        WHERE survey_response #> %s = %s
    """
}


def connect(params):
    def factory():
        try:
            with factory.connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except psycopg2.OperationalError as e:
            factory.connection = psycopg2.connect(**params)
            factory.connection.autocommit = True

        return factory.connection.cursor()

    factory.connection = psycopg2.connect(**params)
    factory.connection.autocommit = True

    return factory


db = connect(
    dict(host=app.config['DB_HOST'],
         port=app.config['DB_PORT'],
         database=app.config['DB_NAME'],
         password=app.config['DB_PASSWORD'],
         user=app.config['DB_USER']))


def get_sql(select=True, path=None, operator=None, query_json=False):
    if not query_json:
        if len(path.split(',')) == 1:
            if select:
                return SQL.get("{}_{}_{}".format('select', operator, path).upper())
            else:
                return SQL.get("{}_{}_{}".format('count', operator, path).upper())
        else:
            raise NotImplementedError
    else:
        if len(path.split(',')) == 1:
            if select:
                return SQL.get("SELECT_FIRST_LEVEL")
            else:
                return SQL.get("COUNT_FIRST_LEVEL")
        elif len(path.split(',')) == 2:
            if select:
                return SQL.get("SELECT_SECOND_LEVEL")
            else:
                return SQL.get("COUNT_SECOND_LEVEL")
        else:
            raise NotImplementedError


def search(criteria):
    page = criteria['page'] - 1
    items_per_page = criteria['items_per_page']
    query_json = criteria['query']['json']
    path = criteria['query']['path']
    operator = criteria['query']['operator']
    value = criteria['query']['value']

    with db() as cursor:
        cursor.itersize = items_per_page

        query = get_sql(True, path, operator, query_json)

        if query_json:
            cursor.execute(query, (path, value))
        else:
            cursor.execute(query, (value, ))

        try:
            cursor.scroll(page * items_per_page)
            return cursor.fetchmany(items_per_page)
        except (psycopg2.ProgrammingError, IndexError):
            return []


def count(criteria):
    query_json = criteria['query']['json']
    path = criteria['query']['path']
    operator = criteria['query']['operator']
    value = criteria['query']['value']

    with db() as cursor:
        query = get_sql(False, path, operator, query_json)

        if query_json:
            cursor.execute(query, (path, value))
        else:
            cursor.execute(query, (value, ))

        res = cursor.fetchone()
        return res[0]


def save_response(survey_response, bound_logger):
    with db() as cursor:
        try:
            cursor.execute(SQL['INSERT_DOC'],
                           {'added_date': datetime.utcnow(),
                            'survey_response': psycopg2.extras.Json(survey_response)})
            return str(cursor.fetchone()[0])
        except psycopg2.Error as e:
            bound_logger.error("Failed to store survey response",
                               exception=str(e))
            return None
