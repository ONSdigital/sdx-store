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
else:
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

SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', default=False)
