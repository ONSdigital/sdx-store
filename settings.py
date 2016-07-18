import os
import logging

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-store: %(message)s"
LOGGING_LEVEL = logging.DEBUG

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
RABBIT_QUEUE = os.getenv('RABBITMQ_QUEUE', 'sdx-survey-notifications')

RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST', 'rabbit'),
    port=os.getenv('RABBITMQ_PORT', 5672),
    user=os.getenv('RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST', '%2f')
)
