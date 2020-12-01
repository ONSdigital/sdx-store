import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from structlog import wrap_logger

import settings

__version__ = "3.15.0"

logging.basicConfig(format=settings.LOGGING_FORMAT,
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    level=settings.LOGGING_LEVEL)

logger = wrap_logger(logging.getLogger(__name__))

logger.info("Starting SDX Store", version=__version__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS

db = SQLAlchemy(app=app)
