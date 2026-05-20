import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from icalendar import Calendar, Event

from config import (
    PUBLIC_HOLIDAYS_ICS_DIR,
    PUBLIC_HOLIDAYS_RESULT_DIR,
    STATE_NAMES,
    WEBSITE_BASE_URL,
)

JSON_RESULT_DIR = Path(PUBLIC_HOLIDAYS_RESULT_DIR)
RESULT_DIR = Path(PUBLIC_HOLIDAYS_ICS_DIR)
STATE_NAME_BY_CODE = STATE_NAMES
ALL_STATE_CODES = set(STATE_NAME_BY_CODE.keys())

os.makedirs(RESULT_DIR, exist_ok=True)


def generate_uid(event_id: str, calendar_slug: str) -> str:
    return f"{event_id}-{calendar_slug}@feiertage.ics.tools"


def format_github_actions_error(file_path: Path, message: str) -> str:
    escaped_message = (
        message.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )
    return f"::error file={file_path.as_posix()}::{escaped_message}"


def load_state_holidays() -> dict[str, dict[str, Any]]:
    aggregated: dict[str, dict[str, Any]] = {}

    for json_file in sorted(JSON_RESULT_DIR.glob("*.json")):
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
            raise RuntimeError(
                format_github_actions_error(json_file, error_message)
            )

        for item in data.get("holidays", []):
            holiday_id = item.get("id")
            if not holiday_id:
                continue

            state_bucket = aggregated.setdefault(
                holiday_id,
                {
                    "id": holiday_id,
                    "name": item.get("name"),
                    "date": item.get("date"),
                    "created": item.get("created"),
                    "modified": item.get("modified"),
                    "sequence": item.get("sequence", 0),
                    "states": set(),
                    "name_counts": Counter(),
                },
            )

            state_bucket["states"].add(federal_state_iso_code)

            if item.get("name"):
                state_bucket["name_counts"][item.get("name")] += 1

            if item.get("date") and (
                state_bucket["date"] is None
                or item.get("date") < state_bucket["date"]
            ):
                state_bucket["date"] = item.get("date")
            if item.get("created") and (
                state_bucket["created"] is None
                or item.get("created") < state_bucket["created"]
            ):
                state_bucket["created"] = item.get("created")
            if item.get("modified") and (
                state_bucket["modified"] is None
                or item.get("modified") > state_bucket["modified"]
            ):
                state_bucket["modified"] = item.get("modified")
            state_bucket["sequence"] += item.get("sequence", 0)

    return aggregated


def select_summary(name_counts: Counter[str], fallback_name: str) -> str:
    if not name_counts:
        return fallback_name

    most_common = name_counts.most_common()
    highest_count = most_common[0][1]
    candidates = sorted(
        [name for name, count in most_common if count == highest_count],
        key=lambda name: name.casefold(),
    )
    return candidates[0]


def sort_state_names(state_codes: set[str]) -> list[str]:
    return sorted(
        (STATE_NAME_BY_CODE[code] for code in state_codes),
        key=lambda name: name.casefold(),
    )


def build_description(state_codes: set[str]) -> str:
    missing_state_codes = ALL_STATE_CODES - state_codes

    if not missing_state_codes:
        return "Gilt in allen Bundesländern"

    if len(missing_state_codes) <= 5:
        missing_state_names = sort_state_names(missing_state_codes)
        return "\n".join(
            ["Gilt in allen Bundesländern außer:"]
            + [f"- {state_name}" for state_name in missing_state_names]
        )

    state_names = sort_state_names(state_codes)
    return "\n".join(["Gilt in:"] + [f"- {state_name}" for state_name in state_names])


def build_calendar(
    calendar_name: str,
    calendar_slug: str,
    items: list[dict[str, Any]],
) -> None:
    result_file = RESULT_DIR / f"{calendar_slug}.ics"

    cal = Calendar()
    cal.add("prodid", "-//ics.tools//ics.tools Feiertage v2.0//DE")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", calendar_name)
    cal.add("name", calendar_name)
    cal.add("x-wr-timezone", "Europe/Berlin")
    cal.add("refresh-interval", "P1D", parameters={"VALUE": "DURATION"})
    cal.add("x-published-ttl", "P1D")
    cal.add("calscale", "GREGORIAN")
    cal.add("source", urljoin(WEBSITE_BASE_URL, result_file.as_posix()))
    cal.add("method", "PUBLISH")

    for item in sorted(items, key=lambda entry: (entry["date"], entry["name"], entry["id"])):
        event = Event()
        event.add("uid", generate_uid(item["id"], calendar_slug))
        event.add("summary", item["name"])

        start_date = datetime.fromisoformat(item["date"]).date()
        end_date = start_date + timedelta(days=1)

        event.add("dtstart", start_date)
        event.add("dtend", end_date)
        event.add("created", datetime.fromisoformat(item["created"]))
        event.add("last-modified", datetime.fromisoformat(item["modified"]))
        event.add("dtstamp", datetime.now(timezone.utc))
        event.add("sequence", item["sequence"])
        event.add("transp", "TRANSPARENT")
        event.add("description", build_description(item["states"]))
        event.add("location", ", ".join(sorted(item["states"])))
        cal.add_component(event)

    with open(result_file, "wb") as output_file:
        output_file.write(cal.to_ical())


def main() -> None:
    holidays_by_id = load_state_holidays()

    all_holidays: list[dict[str, Any]] = []
    bundesweit_holidays: list[dict[str, Any]] = []

    for holiday_id, item in holidays_by_id.items():
        summary = select_summary(item["name_counts"], item["name"])
        normalized_item = {
            "id": holiday_id,
            "name": summary,
            "date": item["date"],
            "created": item["created"],
            "modified": item["modified"],
            "sequence": item["sequence"],
            "states": item["states"],
        }
        all_holidays.append(normalized_item)

        if item["states"] == ALL_STATE_CODES:
            bundesweit_holidays.append(normalized_item)

    build_calendar("Alle Feiertage", "alle", all_holidays)
    build_calendar("Bundesweite Feiertage", "bundesweit", bundesweit_holidays)


if __name__ == "__main__":
    main()
