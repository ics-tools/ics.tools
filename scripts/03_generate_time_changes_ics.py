# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import datetime, timedelta, timezone
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
from time_change_utils import last_sunday

RESULT_DIR = Path(EXTRA_ICS_DIR)
RESULT_FILE = RESULT_DIR / "zeitumstellungen.ics"
CALENDAR_NAME = "Zeitumstellungen"
CALENDAR_SLUG = "zeitumstellungen"

os.makedirs(RESULT_DIR, exist_ok=True)


def generate_uid(event_id: str, calendar_slug: str) -> str:
    return f"{event_id}-{calendar_slug}@zeitumstellungen.ics.tools"


def iter_time_changes(start_year: int, end_year: int):
    for year in range(start_year, end_year + 1):
        yield (
            last_sunday(year, 3),
            "Beginn der Sommerzeit",
            "Die Uhr wird von 02:00 Uhr auf 03:00 Uhr vorgestellt.",
        )
        yield (
            last_sunday(year, 10),
            "Beginn der Winterzeit",
            "Die Uhr wird von 03:00 Uhr auf 02:00 Uhr zurückgestellt.",
        )


def build_calendar() -> None:
    cal = Calendar()
    cal.add("prodid", "-//ics.tools//ics.tools Zeitumstellungen v1.0//DE")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", CALENDAR_NAME)
    cal.add("name", CALENDAR_NAME)
    cal.add("x-wr-caldesc", "Sommer- und Winterzeitumstellung")
    cal.add("description", "Sommer- und Winterzeitumstellung")
    cal.add("x-wr-timezone", "Europe/Berlin")
    cal.add("refresh-interval", "P1Y", parameters={"VALUE": "DURATION"})
    cal.add("x-published-ttl", "P1Y")
    cal.add("calscale", "GREGORIAN")
    cal.add("source", urljoin(WEBSITE_BASE_URL, RESULT_FILE.as_posix()))
    cal.add("method", "PUBLISH")

    now = datetime.now(timezone.utc)
    for change_date, summary, description in iter_time_changes(FETCH_START_YEAR, FETCH_END_YEAR):
        event = Event()
        event.add("uid", generate_uid(change_date.isoformat(), CALENDAR_SLUG))
        event.add("summary", summary)
        event.add("description", description)
        event.add("dtstart", change_date)
        event.add("dtend", change_date + timedelta(days=1))
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