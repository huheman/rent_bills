from datetime import date, datetime, timedelta
from functools import lru_cache

import pytz

from app.core.config import Settings


def get_next_month_start_timestamp(created_at_ms: int) -> int:
    timezone = _get_timezone()
    utc_time = datetime.utcfromtimestamp(created_at_ms / 1000.0)
    local_time = pytz.utc.localize(utc_time).astimezone(timezone)
    next_month = (local_time.replace(day=1) + timedelta(days=32)).replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    utc_next_month = next_month.astimezone(pytz.utc)
    return int(utc_next_month.timestamp() * 1000)


def format_month_str(value: date) -> str:
    return f"{value.year}年{value.month}月"


def as_local_date(timestamp_ms: int) -> date:
    timezone = _get_timezone()
    dt = datetime.utcfromtimestamp(timestamp_ms / 1000.0)
    dt_utc = pytz.utc.localize(dt)
    return dt_utc.astimezone(timezone).date()


@lru_cache(maxsize=1)
def _get_timezone():
    settings = Settings.from_env()
    return pytz.timezone(settings.app_timezone)
