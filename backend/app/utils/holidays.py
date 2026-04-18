from datetime import date

try:
    from chinese_calendar import is_holiday as _is_holiday, is_workday as _is_workday

    def is_holiday(d: date) -> bool:
        try:
            return _is_holiday(d)
        except (NotImplementedError, ValueError):
            return d.weekday() >= 5

    def is_workday(d: date) -> bool:
        try:
            return _is_workday(d)
        except (NotImplementedError, ValueError):
            return d.weekday() < 5

except ImportError:
    def is_holiday(d: date) -> bool:
        return d.weekday() >= 5

    def is_workday(d: date) -> bool:
        return d.weekday() < 5
