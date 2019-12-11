import os
import logging
import json


LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))
LOGGING_FORMAT = "%(asctime)s.%(msecs)06dZ|%(levelname)s: sdx-store: %(message)s"

if os.getenv("CF_DEPLOYMENT", False):
    vcap_services = os.getenv("VCAP_SERVICES")
    parsed_vcap_services = json.loads(vcap_services)
    rds_config = parsed_vcap_services.get('rds')
    DB_URI = rds_config[0].get('credentials').get('uri')
    RESPONSE_RETENTION_DAYS = 90  # Defaulted in CF, (never probably going to be used), but a reminder for if we ever do
else:
    DB_HOST = os.getenv('SDX_STORE_POSTGRES_HOST', 'localhost')
    DB_PORT = os.getenv('SDX_STORE_POSTGRES_PORT', '5433')
    DB_NAME = os.getenv('SDX_STORE_POSTGRES_NAME', 'sdx')
    DB_USER = os.getenv('SDX_STORE_POSTGRES_USER', 'sdx')
    DB_PASSWORD = os.getenv('SDX_STORE_POSTGRES_PASSWORD', 'sdx')
    DB_URI = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER,
                                                  DB_PASSWORD,
                                                  DB_HOST,
                                                  DB_PORT,
                                                  DB_NAME)
    RESPONSE_RETENTION_DAYS = os.getenv('SDX_STORE_RESPONSE_RETENTION_DAYS')   # No default

SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', default=False)
