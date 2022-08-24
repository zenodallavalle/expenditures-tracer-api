import datetime as dt
import pytz
from decimal import Decimal
import warnings

default_tz = None
default_dt_format = "%Y-%m-%d %H:%M%S"


def set_default_tz(tz_string):
    global default_tz
    default_tz = pytz.timezone(tz_string)


def set_default_dt_format(dt_format):
    global default_dt_format
    default_dt_format = dt_format


def datetime_to_timestamp(x):
    if x.tzinfo is None:
        if default_tz is None:
            warnings.warn(
                "You passed a naive datetime instance. By default UTC timezone will be used."
            )
            return int(pytz.utc.localize(x).timestamp())
        else:
            return int(default_tz.localize(x).timestamp())
    else:
        return int(x.timestamp())


def to_timestamp(x, dt_format=None):
    if isinstance(x, int):
        return x
    elif isinstance(x, float):
        return int(x)
    elif isinstance(x, Decimal):
        return int(x)
    elif isinstance(x, dt.datetime):
        return datetime_to_timestamp(x)
    elif isinstance(x, str):
        try:
            dt_x = dt.datetime.strptime(x, dt_format or default_dt_format)
            return datetime_to_timestamp(dt_x)
        except ValueError:
            dt_x = dt.datetime.fromisoformat(x)
            return datetime_to_timestamp(dt_x)
    raise TypeError(
        f"Invalid type for x {type(x)}, must be int, float, Decimal, datetime or string."
    )


def to_datetime(x, tz_info=None):
    if tz_info is not None:
        return dt.datetime.fromtimestamp(x, tz=tz_info)
    else:
        if default_tz is None:
            warnings.warn("You have not set default_tz, datetime returned is naive.")
            return dt.datetime.fromtimestamp(x)
        else:
            return dt.datetime.fromtimestamp(x, tz=default_tz)


def to_iso(x):
    if not isinstance(x, dt.datetime):
        raise TypeError('x must be a dt.datetime instance.')
    return x.astimezone().replace(microsecond=0).isoformat()
