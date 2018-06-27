from openpyxl import Workbook
from typing import List
import time


def create_comments_book(survey_id: str, comments: List) -> Workbook:
    wb = Workbook()
    wb.create_sheet('Exported comments')
    row = 2
    ws = wb.active
    ws.cell(1, 1, survey_id)
    for survey, comment in enumerate(comments):
        row += 1
        ws.cell(row, 1, comment[1])

    return wb
