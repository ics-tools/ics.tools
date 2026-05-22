# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import json
from pathlib import Path
from icalendar import Calendar, Event
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, quote
from config import PUBLIC_HOLIDAYS_ICS_DIR, PUBLIC_HOLIDAYS_RESULT_DIR, WEBSITE_BASE_URL

JSON_RESULT_DIR = Path(PUBLIC_HOLIDAYS_RESULT_DIR)
RESULT_DIR = Path(PUBLIC_HOLIDAYS_ICS_DIR)

os.makedirs(RESULT_DIR, exist_ok=True)


def generate_uid(event_id, state_code):
    return f"{event_id}-{state_code}@feiertage.ics.tools"


def format_github_actions_error(file_path, message):
    escaped_message = (
        message.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )
    return f"::error file={file_path.as_posix()}::{escaped_message}"


for json_file in JSON_RESULT_DIR.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)

    # Validate that filename matches state metadata.
    federal_state = data.get("metadata").get("state")
    federal_state_iso_code = data.get("metadata").get("code")
    expected_filename = f"{federal_state_iso_code}.json"

    if json_file.name != expected_filename:
        error_message = (
            f"Validation error: filename '{json_file.name}' does not match "
            f"state '{data.get('metadata').get('state')}' "
            f"(expected: '{expected_filename}')."
        )
        raise RuntimeError(
            format_github_actions_error(json_file, error_message)
        )

    result_file = RESULT_DIR / f"{federal_state.lower()}.ics"

    cal = Calendar()
    cal.add("prodid", "-//ics.tools//ics.tools Feiertage v2.0//DE")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", f"{federal_state} Feiertage")
    cal.add("name", f"{federal_state} Feiertage")
    cal.add("x-wr-timezone", "Europe/Berlin")
    cal.add("refresh-interval", "P1D", parameters={"VALUE": "DURATION"})
    cal.add("x-published-ttl", "P1D")
    cal.add("calscale", "GREGORIAN")
    cal.add("source", urljoin(WEBSITE_BASE_URL, result_file.as_posix()))
    cal.add("method", "PUBLISH")

    for item in data.get("holidays"):
        event = Event()
        event.add(
            "uid", generate_uid(item.get("id"), federal_state_iso_code)
        )
        event.add("summary", item.get("name"))
        start_date = datetime.fromisoformat(item["date"]).date()
        end_date = start_date + timedelta(days=1)
        event.add("dtstart", start_date)
        event.add("dtend", end_date)
        event.add("created", datetime.fromisoformat(item["created"]))
        event.add("last-modified", datetime.fromisoformat(item["modified"]))
        event.add("dtstamp", datetime.now(timezone.utc))
        event.add("sequence", item["sequence"])
        event.add("transp", "TRANSPARENT")
        cal.add_component(event)

    with open(result_file, "wb") as f:
        f.write(cal.to_ical())
