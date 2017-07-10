import os
import logging


LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))

DB_HOST = os.getenv('SDX_STORE_POSTGRES_HOST', '0.0.0.0')
DB_PORT = os.getenv('SDX_STORE_POSTGRES_PORT', '5432')
DB_NAME = os.getenv('SDX_STORE_POSTGRES_NAME', 'postgres')
DB_USER = os.getenv('SDX_STORE_POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('SDX_STORE_POSTGRES_PASSWORD', 'secret')
DB_URI = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER,
                                              DB_PASSWORD,
                                              DB_HOST,
                                              DB_PORT,
                                              DB_NAME)


RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('SDX_STORE_RABBITMQ_HOST', 'rabbit'),
    port=os.getenv('SDX_STORE_RABBITMQ_PORT', '5672'),
    user=os.getenv('SDX_STORE_RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('SDX_STORE_RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('SDX_STORE_RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URL2 = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('SDX_STORE_RABBITMQ_HOST2', 'rabbit'),
    port=os.getenv('SDX_STORE_RABBITMQ_PORT2', '5433'),
    user=os.getenv('SDX_STORE_RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('SDX_STORE_RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('SDX_STORE_RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URLS = [RABBIT_URL, RABBIT_URL2]

RABBIT_CORA_QUEUE = os.getenv('SDX_STORE_RABBIT_CORA_QUEUE',
                              'sdx-cora-survey-notifications')
RABBIT_CTP_QUEUE = os.getenv('SDX_STORE_RABBIT_CTP_QUEUE',
                             'sdx-ctp-survey-notifications')
RABBIT_CS_QUEUE = os.getenv('SDX_STORE_RABBIT_CS_QUEUE',
                            'sdx-cs-survey-notifications')

SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS',
                                           default=False)
