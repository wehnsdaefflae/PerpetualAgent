# coding=utf-8
from datetime import datetime


def get_current_date_time() -> str:
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_datetime
