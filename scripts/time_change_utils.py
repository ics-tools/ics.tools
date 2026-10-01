from datetime import date, timedelta


def last_sunday(year: int, month: int) -> date:
    month_end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return month_end - timedelta(days=(month_end.weekday() + 1) % 7)