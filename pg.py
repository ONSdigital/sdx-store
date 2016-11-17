from datetime import datetime

import psycopg2
import psycopg2.extras
import settings

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


db = None

db_config = {'host': settings.DB_HOST,
             'port': settings.DB_PORT,
             'database': settings.DB_NAME,
             'password': settings.DB_PASSWORD,
             'user': settings.DB_USER}


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


def use_db(func=None):
    def inner(*args, **kwargs):
        global db
        if not db:
            db = connect(db_config)
        return func(*args, **kwargs)
    return inner


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


def file_to_string(path):
    with open(path, 'r') as f:
        return f.read()


@use_db
def create_table():
    with db() as cursor:
        cursor.execute(file_to_string('./setup.sql'))


@use_db
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


@use_db
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


@use_db
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
