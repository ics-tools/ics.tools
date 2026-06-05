# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

from icalendar import Calendar, Event

from config import (
    PUBLIC_HOLIDAYS_ICS_DIR,
    PUBLIC_HOLIDAYS_RESULT_DIR,
    STATE_NAMES,
    WEBSITE_BASE_URL,
)

JSON_RESULT_FILE = Path(PUBLIC_HOLIDAYS_RESULT_DIR) / "de.json"
RESULT_DIR = Path(PUBLIC_HOLIDAYS_ICS_DIR)
STATE_NAME_BY_CODE = STATE_NAMES
STATE_CODE_ORDER = list(STATE_NAME_BY_CODE.keys())
ALL_STATE_CODES = set(STATE_CODE_ORDER)

os.makedirs(RESULT_DIR, exist_ok=True)


def generate_uid(event_id: str, calendar_slug: str) -> str:
    return f"{event_id}-{calendar_slug}@feiertage.ics.tools"


def load_json_file(filepath: Path, default_fallback: Any) -> Any:
    if not filepath.exists():
        return default_fallback

    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except json.JSONDecodeError:
        return default_fallback


def load_public_holidays() -> list[dict[str, Any]]:
    data = load_json_file(JSON_RESULT_FILE, default_fallback={})
    holidays = data.get("holidays", []) if isinstance(data, dict) else []

    return [item for item in holidays if isinstance(item, dict)]


def ordered_state_codes(state_codes: Iterable[str], own_state_code: str | None = None) -> list[str]:
    unique_codes = {code for code in state_codes if code in STATE_NAME_BY_CODE}
    alphabetical_codes = sorted(unique_codes, key=lambda code: STATE_NAME_BY_CODE[code].casefold())

    if own_state_code and own_state_code in unique_codes:
        return [own_state_code] + [code for code in alphabetical_codes if code != own_state_code]

    return alphabetical_codes


def build_description(state_codes: list[str], own_state_code: str | None = None) -> str:
    ordered_codes = ordered_state_codes(state_codes, own_state_code=own_state_code)
    if set(ordered_codes) == ALL_STATE_CODES:
        return "Gilt in allen Bundesländern."

    state_names = [STATE_NAME_BY_CODE[code] for code in ordered_codes]
    return "\n".join(["Gilt in:"] + [f"- {state_name}" for state_name in state_names])


def build_location(state_codes: list[str], own_state_code: str | None = None) -> str:
    ordered_codes = ordered_state_codes(state_codes, own_state_code=own_state_code)
    if set(ordered_codes) == ALL_STATE_CODES:
        return "Bundesweit"

    return ", ".join(ordered_codes)


def build_calendar(
    calendar_name: str,
    calendar_slug: str,
    items: list[dict[str, Any]],
    own_state_code: str | None = None,
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

    for item in sorted(
        items,
        key=lambda entry: (entry["startDate"], entry["endDate"], entry["name"], entry["id"]),
    ):
        event = Event()
        event.add(
            "uid",
            generate_uid(
                item["id"],
                own_state_code if own_state_code is not None else calendar_slug,
            ),
        )
        event.add("summary", item["name"])

        start_date = datetime.fromisoformat(item["startDate"]).date()
        inclusive_end_date = datetime.fromisoformat(item["endDate"]).date()
        if inclusive_end_date < start_date:
            raise RuntimeError(
                f"Invalid holiday range for {item.get('id')}: endDate before startDate."
            )

        # RFC5545 all-day events use an exclusive DTEND boundary.
        exclusive_end_date = inclusive_end_date + timedelta(days=1)

        event.add("dtstart", start_date)
        event.add("dtend", exclusive_end_date)
        event.add("created", datetime.fromisoformat(item["created"]))
        event.add("last-modified", datetime.fromisoformat(item["modified"]))
        event.add("dtstamp", datetime.now(timezone.utc))
        event.add("sequence", item["sequence"])
        event.add("transp", "TRANSPARENT")
        event.add("description", build_description(item["states"], own_state_code=own_state_code))
        event.add("location", build_location(item["states"], own_state_code=own_state_code))
        cal.add_component(event)

    with open(result_file, "wb") as output_file:
        output_file.write(cal.to_ical())


def slugify_state_name(state_name: str) -> str:
    return state_name.lower()


def main() -> None:
    holidays = load_public_holidays()

    normalized_holidays: list[dict[str, Any]] = []
    for item in holidays:
        states = item.get("states", [])
        if not isinstance(states, list):
            states = []

        filtered_states = [code for code in STATE_CODE_ORDER if code in set(states)]
        if not filtered_states:
            continue

        normalized_holidays.append(
            {
                "id": item["id"],
                "name": item["name"],
                "startDate": item["startDate"],
                "endDate": item["endDate"],
                "created": item["created"],
                "modified": item["modified"],
                "sequence": item["sequence"],
                "states": filtered_states,
            }
        )

    for state_code, state_name in STATE_NAME_BY_CODE.items():
        state_items = [item for item in normalized_holidays if state_code in item["states"]]
        build_calendar(
            calendar_name=f"{state_name} Feiertage",
            calendar_slug=slugify_state_name(state_name),
            items=state_items,
            own_state_code=state_code,
        )

    all_holidays = list(normalized_holidays)
    bundesweit_holidays = [
        item for item in normalized_holidays if set(item["states"]) == ALL_STATE_CODES
    ]

    build_calendar("Alle Feiertage", "alle", all_holidays)
    build_calendar("Bundesweite Feiertage", "bundesweit", bundesweit_holidays)


if __name__ == "__main__":
    main()
