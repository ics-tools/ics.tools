import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

from icalendar import Calendar, Event
from config import (
    SCHOOL_HOLIDAYS_ICS_DIR,
    SCHOOL_HOLIDAYS_RESULT_DIR,
    WEBSITE_BASE_URL,
)

JSON_RESULT_DIR = Path(SCHOOL_HOLIDAYS_RESULT_DIR)
RESULT_DIR = Path(SCHOOL_HOLIDAYS_ICS_DIR)

os.makedirs(RESULT_DIR, exist_ok=True)


def generate_uid(event_id: str, state_code: str) -> str:
    return f"{event_id}-{state_code}@ferien.ics.tools"


def format_github_actions_error(file_path: Path, message: str) -> str:
    escaped_message = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::error file={file_path.as_posix()}::{escaped_message}"


def main() -> None:
    for json_file in JSON_RESULT_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)

        metadata = data.get("metadata", {})
        federal_state = metadata.get("state")
        federal_state_iso_code = metadata.get("code")
        expected_filename = f"{federal_state_iso_code}.json"

        if json_file.name != expected_filename:
            error_message = (
                f"Validation error: filename '{json_file.name}' does not match "
                f"state '{federal_state}' (expected: '{expected_filename}')."
            )
            raise RuntimeError(format_github_actions_error(json_file, error_message))

        result_file = RESULT_DIR / f"{federal_state.lower()}.ics"

        cal = Calendar()
        cal.add("prodid", "-//ics.tools//ics.tools Schulferien v2.0//DE")
        cal.add("version", "2.0")
        cal.add("x-wr-calname", f"{federal_state} Schulferien")
        cal.add("name", f"{federal_state} Schulferien")
        cal.add("x-wr-timezone", "Europe/Berlin")
        cal.add("refresh-interval", "P1D", parameters={"VALUE": "DURATION"})
        cal.add("x-published-ttl", "P1D")
        cal.add("calscale", "GREGORIAN")
        cal.add("source", urljoin(WEBSITE_BASE_URL, result_file.as_posix()))
        cal.add("method", "PUBLISH")

        for item in data.get("holidays", []):
            event = Event()
            event.add("uid", generate_uid(item.get("id"), federal_state_iso_code))
            event.add("SUMMARY", item.get("name"))

            start_date = datetime.fromisoformat(item["date"]).date()
            inclusive_end_date = datetime.fromisoformat(item["endDate"]).date()
            if inclusive_end_date < start_date:
                raise RuntimeError(
                    format_github_actions_error(
                        json_file,
                        f"Invalid holiday range for {item.get('id')}: endDate before date.",
                    )
                )

            # RFC5545 all-day events use an exclusive DTEND boundary.
            exclusive_end_date = inclusive_end_date + timedelta(days=1)

            event.add("DTSTART", start_date)
            event.add("DTEND", exclusive_end_date)
            event.add("CREATED", datetime.fromisoformat(item["created"]))
            event.add("LAST-MODIFIED", datetime.fromisoformat(item["modified"]))
            event.add("DTSTAMP", datetime.now(timezone.utc))
            event.add("SEQUENCE", item["sequence"])
            event.add("transp", "TRANSPARENT")
            cal.add_component(event)

        with open(result_file, "wb") as output_file:
            output_file.write(cal.to_ical())


if __name__ == "__main__":
    main()
