import os
import sys

parent_dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_path)

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.models import SurveyResponse
import settings

try:
    db = create_engine(settings.DB_URI)
    Session = sessionmaker(db)
    session = Session()
    base = declarative_base()
except SQLAlchemyError as e:
    print(e)
    raise


def reset_store_data(tx_id):
    """Remove invalid key from data and
       set invalid column to False"""

    records = session.query(SurveyResponse).filter(
        SurveyResponse.tx_id == tx_id)

    for record in records:
        if record.data.get('invalid'):
            record.data.pop('invalid')  # Remove 'invalid' key

        response = SurveyResponse(tx_id=tx_id,
                                  invalid=False,  # Set invalid column to False
                                  data=record.data)

        save_updated_record(response)
        print("TX_ID {} updated".format(tx_id))


def save_updated_record(response):
    try:
        session.merge(response)
        session.commit()
    except (SQLAlchemyError, IntegrityError) as e:
        session.rollback()
        raise e


if __name__ == "__main__":
    with open('tx_ids', 'r') as fp:
        lines = list(fp)

    if not lines:
        sys.exit("No tx_ids in file, exiting script")
    for tx_id in lines:
        try:
            reset_store_data(tx_id.rstrip())
        except (SQLAlchemyError, IntegrityError) as e:
            print("TX_ID {} FAILED update".format(tx_id))
            print(e)
            raise
