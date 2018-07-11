import os
import logging
import time

from openpyxl import Workbook
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def create_comments_book(survey_id: str, comments) -> str:
    logger.info("Generating excel file")
    wb = Workbook()
    wb.create_sheet('Exported comments')
    row = 2
    ws = wb.active
    ws.cell(1, 1, "Survey ID: {}".format(survey_id))
    ws.cell(1, 2, "Comments found: {}".format(str(len(comments))))
    for comment in comments:
        row += 1
        ws.cell(row, 1, comment.data['data']['146'])
        ws.cell(row, 2, comment.data['submitted_at'])

    filename = os.path.join(os.getcwd(), "comments_" +
                            "".join(time.strftime("%Y%m%d-%H%M%S")) + ".xlsx")
    logger.info("Excel file name", filename=filename)

    wb.save(filename)
    wb.close()
    return filename
