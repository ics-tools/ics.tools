# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from config import (
    IGNORED_RAW_TAGS,
    SCHOOL_HOLIDAY_GROUPS_BY_STATE,
    SCHOOL_HOLIDAYS_OVERRIDE_DIR,
    SCHOOL_HOLIDAYS_RAW_DIR,
    SCHOOL_HOLIDAYS_RESULT_DIR,
    STATE_NAMES,
)


def calculate_md5(name: str, start_date: str, end_date: str) -> str:
    """Generates a stable MD5 hash for the core school holiday content."""
    content = f"{name}|{start_date}|{end_date}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def get_now_iso() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json_file(filepath: str, default_fallback: Any) -> Any:
    """Safely loads a JSON file, returning a fallback if it does not exist."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    return default_fallback


def should_ignore_entry(entry: Dict[str, Any]) -> bool:
    """Returns True when the raw entry has a tag configured to be skipped."""
    tags = entry.get("tags")
    if not isinstance(tags, list):
        return False

    return any(tag in IGNORED_RAW_TAGS for tag in tags)


def get_entry_group_codes(entry: Dict[str, Any]) -> List[str]:
    """Extracts group codes from a raw entry, ignoring malformed items."""
    groups = entry.get("groups")
    if not isinstance(groups, list):
        return []

    group_codes: List[str] = []
    for group in groups:
        if isinstance(group, dict):
            group_code = group.get("code")
            if group_code:
                group_codes.append(group_code)
        elif isinstance(group, str) and group:
            group_codes.append(group)

    return group_codes


def should_keep_entry_for_state(entry: Dict[str, Any], state_code: str) -> bool:
    """Keeps all entries when no state filter exists or when an entry has no groups."""
    allowed_groups = SCHOOL_HOLIDAY_GROUPS_BY_STATE.get(state_code)
    if not allowed_groups:
        return True

    entry_groups = get_entry_group_codes(entry)
    if not entry_groups:
        return True

    return any(group_code in allowed_groups for group_code in entry_groups)


def extract_name(
    name_list: Optional[List[Dict[str, str]]],
    entry_id: str,
    state: str,
    year: int
) -> str:
    """Extracts the German text from the API name array with fallback."""
    if not name_list or not isinstance(name_list, list) or len(name_list) == 0:
        print(
            f"::warning title=Missing Name,file={state}.json::No name found for school holiday {entry_id} in {state}. Using 'Unknown'."
        )
        return f"Unknown {year} {STATE_NAMES[state]}"

    for item in name_list:
        text = item.get("text")
        if item.get("language") == "DE" and text:
            return f"{text} {year} {STATE_NAMES[state]}"

    fallback_name = name_list[0].get("text", "Unknown")
    print(
        f"::warning title=Missing German Name,file={state}.json::German name missing for {entry_id} in {state}. Falling back to: {fallback_name}"
    )
    return f"{fallback_name} {year} {STATE_NAMES[state]}"


def apply_overrides(
    working_data: Dict[str, Dict[str, Any]], overrides: Dict[str, List[Dict[str, Any]]]
) -> None:
    """Applies REMOVE, MODIFY, and NEW overrides in-place to the working data."""

    for remove_id in overrides.get("remove", []):
        if remove_id in working_data:
            del working_data[remove_id]

    for mod in overrides.get("modify", []):
        entry_id = mod.get("id")
        if entry_id in working_data:
            if "name" in mod:
                working_data[entry_id]["name"] = mod["name"]
            if "startDate" in mod:
                working_data[entry_id]["date"] = mod["startDate"]
            if "endDate" in mod:
                working_data[entry_id]["endDate"] = mod["endDate"]

    for new_entry in overrides.get("new", []):
        entry_id = new_entry.get("id")
        if not entry_id:
            print("::warning::New override entry is missing an 'id'. Skipping.")
            continue

        start_date = new_entry.get("startDate")
        end_date = new_entry.get("endDate", start_date)

        working_data[entry_id] = {
            "id": entry_id,
            "name": new_entry.get("name"),
            "date": start_date,
            "endDate": end_date,
        }


def enrich_with_metadata(
    state_code: str,
    state_name: str,
    working_data: Dict[str, Dict[str, Any]],
    previous_memory: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compares current data with previous memory to generate sequence numbers and timestamps."""
    final_entries = []
    timestamp_now = get_now_iso()

    for entry_id, data in working_data.items():
        current_md5 = calculate_md5(data["name"], data["date"], data["endDate"])
        previous = previous_memory.get(entry_id)

        final_entry: Dict[str, Any] = {**data, "md5": current_md5}

        if previous:
            if previous.get("md5") == current_md5:
                final_entry.update(
                    {
                        "created": previous.get("created"),
                        "modified": previous.get("modified"),
                        "sequence": previous.get("sequence"),
                    }
                )
            else:
                print(f"  Change detected: {data['name']} ({entry_id})")
                final_entry.update(
                    {
                        "created": previous.get("created"),
                        "modified": timestamp_now,
                        "sequence": previous.get("sequence", 0) + 1,
                    }
                )
        else:
            final_entry.update(
                {
                    "created": timestamp_now,
                    "modified": timestamp_now,
                    "sequence": 0,
                }
            )

        final_entries.append(final_entry)

    final_entries.sort(key=lambda x: (x["date"], x["endDate"]))

    return {
        "$schema": "../../schema/school-holidays.schema.json",
        "metadata": {"state": state_name, "code": state_code},
        "holidays": final_entries,
    }


def process_state(state_code: str, state_name: str) -> None:
    """Handles the complete processing pipeline for a single state."""
    print(f"::group::Merging school holidays for {state_name} ({state_code})")

    raw_path = os.path.join(SCHOOL_HOLIDAYS_RAW_DIR, f"{state_code}.json")
    override_path = os.path.join(SCHOOL_HOLIDAYS_OVERRIDE_DIR, f"{state_code}.json")
    result_path = os.path.join(SCHOOL_HOLIDAYS_RESULT_DIR, f"{state_code}.json")

    raw_entries = load_json_file(raw_path, default_fallback=[])
    overrides = load_json_file(
        override_path, default_fallback={"new": [], "modify": [], "remove": []}
    )

    previous_data = load_json_file(result_path, default_fallback=[])
    if isinstance(previous_data, dict):
        previous_list = previous_data.get("holidays", [])
    else:
        previous_list = previous_data

    previous_memory = {
        item["id"]: item for item in previous_list if isinstance(item, dict) and "id" in item
    }

    working_data = {}
    for entry in raw_entries:
        if entry.get("regionalScope") == "Local":
            continue
        if should_ignore_entry(entry):
            continue
        if not should_keep_entry_for_state(entry, state_code):
            continue

        entry_id = entry.get("id")
        if not entry_id:
            continue

        start_date = entry.get("startDate")
        end_date = entry.get("endDate", start_date)

        working_data[entry_id] = {
            "id": entry_id,
            "name": extract_name(entry.get("name"), entry_id, state_code, int(start_date[:4])),
            "date": start_date,
            "endDate": end_date,
        }

    apply_overrides(working_data, overrides)

    final_result = enrich_with_metadata(
        state_code=state_code,
        state_name=state_name,
        working_data=working_data,
        previous_memory=previous_memory,
    )

    with open(result_path, "w", encoding="utf-8") as file_handle:
        json.dump(final_result, file_handle, ensure_ascii=False, indent=2)

    print(f"Finished {state_name} ({state_code})")
    print("::endgroup::")


def main() -> None:
    os.makedirs(SCHOOL_HOLIDAYS_RESULT_DIR, exist_ok=True)
    print("Starting school holiday merge process with MD5 hashing")

    for state_code, state_name in STATE_NAMES.items():
        process_state(state_code, state_name)

    print("School holiday merge process completed.")


if __name__ == "__main__":
    main()
