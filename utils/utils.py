from typing import Any
from datetime import date, time, timedelta
from sqlalchemy import Integer, BigInteger, Date, Time, Boolean
from services.google_services import GoogleDrive


def combine_lesson_info(lesson: dict) -> str:
    if lesson['is_work'] is not None:
        is_work = '❗️ '
    else:
        is_work = ''
    day = date.strftime(lesson['date'], '%d.%m')
    start_time = time.strftime(lesson['time'], '%H:%M')
    course_title = lesson['course_title']
    number = lesson['number']
    lesson_title = lesson['lesson_title']
    return f'{is_work}{day} {start_time} {course_title} {number} "{lesson_title}"'

def get_first_day_of_month(month: int) -> date:
    year = date.today().year
    return date(year, month, 1)

def get_last_day_of_month(month: int) -> date:
    year = date.today().year
    return date(year, month + 1, 1) - timedelta(days=1)


def convert_value(value: Any, column_type: type) -> Any:
    
    if value == '':
        value = None
        return None
    if isinstance(column_type, Integer) or isinstance(column_type, BigInteger):
        value = int(value)
    elif isinstance(column_type, Boolean):
        value = bool(value)
    elif isinstance(column_type, Date):
        value = date.fromisoformat(value)
    elif isinstance(column_type, Time):
        value = time.fromisoformat(value)
    return value