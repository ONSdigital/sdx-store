from pymongo import MongoClient
import pymongo.errors


def get_db_responses(config, logger, invalid_flag=False):
    try:
        mongo_client = MongoClient(config['MONGODB_URL'])
        if invalid_flag:
            return mongo_client.sdx_store.invalid_responses

        return mongo_client.sdx_store.responses
    except pymongo.errors.OperationFailure as e:
        logger.error("Failed to store survey response", exception=str(e))
        return None
