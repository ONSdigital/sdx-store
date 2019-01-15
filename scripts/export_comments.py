import os
from string import ascii_lowercase
import sys
parent_dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_path)

from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
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


def create_comments_excel_file(survey_id, period, submissions):
    """Extract comments from submissions and write them to an excel file"""
    print("Generating Excel file")
    workbook = Workbook()
    row = 2
    surveys_with_comments_count = 0
    ws = workbook.active

    for submission in submissions:
        comment = submission.data['data'].get('146')

        boxes_selected = ""
        for key in ('146' + letter for letter in ascii_lowercase[1:]):
            if key in submission.data['data'].keys():
                boxes_selected = boxes_selected + key + ' '

        if not comment:
            continue
        row += 1
        surveys_with_comments_count += 1
        ws.cell(row, 1, submission.data['metadata']['ru_ref'])
        ws.cell(row, 2, submission.data['collection']['period'])
        ws.cell(row, 3, boxes_selected)
        ws.cell(row, 4, comment)

    ws.cell(1, 1, "Survey ID: {}".format(survey_id))
    ws.cell(1, 2, "Comments found: {}".format(surveys_with_comments_count))
    print("{} out of {} submissions had comments".format(surveys_with_comments_count, len(submissions)))

    parent_dir_path = os.path.dirname(
        os.path.dirname(os.path.realpath(__file__)))
    filename = os.path.join(parent_dir_path, "{}_{}.xlsx".format(survey_id, period))
    workbook.save(filename)
    workbook.close()
    print("Excel file {} generated".format(filename))


def get_all_submissions(survey_id, period):
    """Get all submissions that match the survey_id and period supplied"""
    survey_records = session.query(SurveyResponse).filter(
        SurveyResponse.data['survey_id'].astext == survey_id)
    records = survey_records.filter(
        SurveyResponse.data['collection']['period'].astext == period).all()
    print("Retrieved {} submissions".format(len(records)))
    return records


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Either survey id or period is missing")

    survey_id = sys.argv[1]
    period = sys.argv[2]

    print('Survey id is {}'.format(survey_id))
    print('Period is {}'.format(period))

    try:
        submissions = get_all_submissions(survey_id, period)
    except SQLAlchemyError as e:
        print(e)
        raise

    if submissions:
        create_comments_excel_file(survey_id, period, submissions)
    else:
        print("No submissions, exiting script")
