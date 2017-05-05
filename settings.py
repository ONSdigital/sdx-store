import os
import logging

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-store: %(message)s"
LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))

DB_HOST = os.getenv('SDX_STORE_POSTGRES_HOST')
DB_PORT = os.getenv('SDX_STORE_POSTGRES_PORT')
DB_NAME = os.getenv('SDX_STORE_POSTGRES_NAME')
DB_USER = os.getenv('SDX_STORE_POSTGRES_USER')
DB_PASSWORD = os.getenv('SDX_STORE_POSTGRES_PASSWORD')
DB_URI = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER,
                                              DB_PASSWORD,
                                              DB_HOST,
                                              DB_PORT,
                                              DB_NAME)

RABBIT_CS_QUEUE = os.getenv('RABBIT_CS_QUEUE')
RABBIT_CTP_QUEUE = os.getenv('RABBIT_CTP_QUEUE')
RABBIT_CORA_QUEUE = os.getenv('RABBIT_CORA_QUEUE')


RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST'),
    port=os.getenv('RABBITMQ_PORT'),
    user=os.getenv('RABBITMQ_DEFAULT_USER'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
)

RABBIT_URL2 = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST2'),
    port=os.getenv('RABBITMQ_PORT2'),
    user=os.getenv('RABBITMQ_DEFAULT_USER'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
)

RABBIT_URLS = [RABBIT_URL, RABBIT_URL2]

SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS',
                                           default=False)
