import os

from flask import logging
from openpyxl import Workbook
from typing import List
import time

from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def create_comments_book(survey_id: str, comments: List) -> str:
    logger.info("Generation excel file ")
    wb = Workbook()
    wb.create_sheet('Exported comments')
    row = 2
    ws = wb.active
    ws.cell(1, 1, survey_id)

    for survey, comment in enumerate(comments):
        row += 1
        ws.cell(row, 1, comment[1])

    logger.info("generation file name ")

    filename = os.path.join(os.getcwd(),  "comments_" + "".join(time.strftime("%Y%m%d-%H%M%S")) + ".xsl")
    logger.info("File name is : " + filename)

    wb.save(filename)
    wb.close()

    return filename
