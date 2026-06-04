# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
from urllib.parse import urljoin

from icalendar import Calendar, Event

from config import (
    FETCH_END_YEAR,
    FETCH_START_YEAR,
    EXTRA_ICS_DIR,
    WEBSITE_BASE_URL,
)

RESULT_DIR = Path(EXTRA_ICS_DIR)
RESULT_FILE = RESULT_DIR / "kalenderwochen.ics"
CALENDAR_NAME = "Kalenderwochen"
CALENDAR_SLUG = "kw"

os.makedirs(RESULT_DIR, exist_ok=True)


def generate_uid(event_id: str, calendar_slug: str) -> str:
    return f"{event_id}-{calendar_slug}@kalenderwochen.ics.tools"


def iter_mondays(start_date: date, end_date: date):
    current_date = start_date + timedelta(days=(7 - start_date.weekday()) % 7)

    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=7)


def build_calendar() -> None:
    cal = Calendar()
    cal.add("prodid", "-//ics.tools//ics.tools Kalenderwochen v1.1//DE")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", CALENDAR_NAME)
    cal.add("name", CALENDAR_NAME)
    cal.add("x-wr-caldesc", "ISO-8601-Kalenderwochen")
    cal.add("description", "ISO-8601-Kalenderwochen")
    cal.add("x-wr-timezone", "Europe/Berlin")
    cal.add("refresh-interval", "P1W", parameters={"VALUE": "DURATION"})
    cal.add("x-published-ttl", "P1W")
    cal.add("calscale", "GREGORIAN")
    cal.add("source", urljoin(WEBSITE_BASE_URL, RESULT_FILE.as_posix()))
    cal.add("method", "PUBLISH")

    now = datetime.now(timezone.utc)
    start_date = date(FETCH_START_YEAR, 1, 1)
    end_date = date(FETCH_END_YEAR, 12, 31)

    for monday in iter_mondays(start_date, end_date):
        week_number = monday.isocalendar().week

        event = Event()
        event.add("uid", generate_uid(monday.isoformat(), CALENDAR_SLUG))
        event.add("summary", f"KW {week_number:02d}")
        event.add("description", f"Kalenderwoche {week_number:02d}")
        event.add("dtstart", monday)
        event.add("dtend", monday + timedelta(days=1))
        event.add("created", now)
        event.add("last-modified", now)
        event.add("dtstamp", now)
        event.add("sequence", 0)
        event.add("transp", "TRANSPARENT")
        cal.add_component(event)

    with open(RESULT_FILE, "wb") as output_file:
        output_file.write(cal.to_ical())


def main() -> None:
    build_calendar()


if __name__ == "__main__":
    main()