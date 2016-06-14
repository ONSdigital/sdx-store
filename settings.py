import logging
import os

logger = logging.getLogger(__name__)

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: %(message)s"
LOGGING_LOCATION = "logs/store.log"
LOGGING_LEVEL = logging.DEBUG

# Default to true, cast to boolean
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
