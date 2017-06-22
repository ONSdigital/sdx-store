import json
import os
import logging


LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))

env_vars = os.getenv('VCAP_SERVICES')
rmq = json.loads(env_vars)['rabbitmq'][0]
RABBIT_URL = rmq['credentials']['protocols']['amqp']['uri']

psql = json.loads(env_vars)['rds'][0]
DB_URI = psql['credentials']['uri']

RABBIT_URLS = [RABBIT_URL]

RABBIT_CORA_QUEUE = os.getenv('SDX_STORE_RABBIT_CORA_QUEUE',
                              'sdx-cora-survey-notifications')
RABBIT_CTP_QUEUE = os.getenv('SDX_STORE_RABBIT_CTP_QUEUE',
                             'sdx-ctp-survey-notifications')
RABBIT_CS_QUEUE = os.getenv('SDX_STORE_RABBIT_CS_QUEUE',
                            'sdx-cs-survey-notifications')

SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS',
                                                                               default=False)
