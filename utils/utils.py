from typing import Any
from datetime import date, time
from sqlalchemy import Integer, BigInteger, String, Date, Time, Boolean


def convert_value(value: Any, column_type: type) -> Any:
    
    if value == '':
        value = None
    if isinstance(column_type, Integer) or isinstance(column_type, BigInteger):
        value = int(value)
    elif isinstance(column_type, Boolean):
        value = bool(value)
    elif isinstance(column_type, Date):
        value = date.fromisoformat(value)
    elif isinstance(column_type, Time):
        value = time.fromisoformat(value)
    return value