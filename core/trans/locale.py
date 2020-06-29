from datetime import datetime, date, time, tzinfo, timedelta
from babel import Locale as BabelLocale
from babel.dates import format_datetime, format_date, format_time, format_timedelta

__all__ = ['Locale']


class Locale(BabelLocale):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def datetime(self, dt: datetime, tz: tzinfo = None) -> str:
        return format_datetime(dt, 'short', tz, self)

    def datetime_long(self, dt: datetime, tz: tzinfo = None) -> str:
        return format_datetime(dt, 'long', tz, self)

    def date(self, d: date) -> str:
        return format_date(d, 'short', self)

    def date_long(self, d: date) -> str:
        return format_date(d, 'long', self)

    def time(self, t: time, tz: tzinfo = None) -> str:
        return format_time(t, 'short', tz, self)

    def timedelta(self, delta: timedelta, granularity: str = 'second', add_direction: bool = False) -> str:
        return format_timedelta(delta, granularity, add_direction=add_direction, locale=self)
