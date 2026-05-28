# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from config import (
    PUBLIC_HOLIDAYS_OVERRIDE_DIR,
    PUBLIC_HOLIDAYS_RAW_DIR,
    PUBLIC_HOLIDAYS_RESULT_DIR,
    STATE_CODES,
)

RAW_PATH = os.path.join(PUBLIC_HOLIDAYS_RAW_DIR, "de.json")
OVERRIDE_PATH = os.path.join(PUBLIC_HOLIDAYS_OVERRIDE_DIR, "de.json")
RESULT_PATH = os.path.join(PUBLIC_HOLIDAYS_RESULT_DIR, "de.json")

STATE_CODE_ORDER = list(STATE_CODES)
STATE_CODE_SET = set(STATE_CODES)
ALL_STATE_CODES = list(STATE_CODES)


def get_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json_file(filepath: str, default_fallback: Any) -> Any:
    if not os.path.exists(filepath):
        return default_fallback

    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except json.JSONDecodeError:
        return default_fallback


def extract_name(name_list: Optional[List[Dict[str, str]]], entry_id: str) -> str:
    if not name_list or not isinstance(name_list, list):
        print(f"::warning title=Missing Name::No name found for public holiday {entry_id}. Using 'Unknown'.")
        return "Unknown"

    for item in name_list:
        if item.get("language") == "DE" and item.get("text"):
            return item["text"]

    fallback_name = name_list[0].get("text", "Unknown")
    print(
        f"::warning title=Missing German Name::German name missing for {entry_id}. Falling back to: {fallback_name}"
    )
    return fallback_name


def normalize_state_codes(raw_states: Iterable[str]) -> List[str]:
    unique_codes = {state_code for state_code in raw_states if state_code in STATE_CODE_SET}
    return [state_code for state_code in STATE_CODE_ORDER if state_code in unique_codes]


def get_entry_states(entry: Dict[str, Any]) -> List[str]:
    if entry.get("nationwide") is True:
        return list(STATE_CODE_ORDER)

    subdivisions = entry.get("subdivisions")
    if not isinstance(subdivisions, list):
        return []

    state_codes: List[str] = []
    for subdivision in subdivisions:
        if not isinstance(subdivision, dict):
            continue

        short_name = subdivision.get("shortName")
        if isinstance(short_name, str) and short_name in STATE_CODE_SET:
            state_codes.append(short_name)

    return normalize_state_codes(state_codes)


def calculate_md5(name: str, start_date: str, end_date: str, states: List[str]) -> str:
    content = json.dumps(
        {
            "name": name,
            "startDate": start_date,
            "endDate": end_date,
            "states": states,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def should_keep_entry(entry: Dict[str, Any]) -> bool:
    if entry.get("regionalScope") == "Local":
        return False

    if entry.get("type") not in (None, "Public"):
        return False

    return True


def build_working_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    entry_id = entry.get("id")
    start_date = entry.get("startDate")
    end_date = entry.get("endDate") or start_date

    if not entry_id or not start_date or not end_date:
        return None

    states = get_entry_states(entry)
    if not states:
        return None

    return {
        "id": entry_id,
        "name": extract_name(entry.get("name"), entry_id),
        "startDate": start_date,
        "endDate": end_date,
        "states": states,
    }


def apply_overrides(
    working_data: Dict[str, Dict[str, Any]], overrides: Dict[str, List[Dict[str, Any]]]
) -> None:
    for remove_id in overrides.get("remove", []):
        if remove_id in working_data:
            del working_data[remove_id]

    for mod in overrides.get("modify", []):
        entry_id = mod.get("id")
        if entry_id not in working_data:
            continue

        if "name" in mod:
            working_data[entry_id]["name"] = mod["name"]

        if "startDate" in mod:
            working_data[entry_id]["startDate"] = mod["startDate"]
            if "endDate" not in mod:
                working_data[entry_id]["endDate"] = mod["startDate"]

        if "endDate" in mod:
            working_data[entry_id]["endDate"] = mod["endDate"]

        if "states" in mod:
            states = normalize_state_codes(mod["states"])
            if states:
                working_data[entry_id]["states"] = states

    for new_entry in overrides.get("new", []):
        entry_id = new_entry.get("id")
        start_date = new_entry.get("startDate")
        end_date = new_entry.get("endDate") or start_date
        states = normalize_state_codes(new_entry.get("states", []))

        if not entry_id or not start_date or not end_date or not states:
            print(f"::warning::Skipping invalid public holiday override entry: {entry_id!r}")
            continue

        working_data[entry_id] = {
            "id": entry_id,
            "name": new_entry.get("name", "Unknown"),
            "startDate": start_date,
            "endDate": end_date,
            "states": states,
        }


def enrich_with_metadata(
    working_data: Dict[str, Dict[str, Any]],
    previous_memory: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    final_entries: List[Dict[str, Any]] = []
    timestamp_now = get_now_iso()

    for entry_id, data in working_data.items():
        current_md5 = calculate_md5(
            data["name"],
            data["startDate"],
            data["endDate"],
            data["states"],
        )
        previous = previous_memory.get(entry_id)

        final_entry: Dict[str, Any] = {**data, "md5": current_md5}

        if previous:
            if previous.get("md5") == current_md5:
                final_entry["created"] = previous.get("created") or timestamp_now
                final_entry["modified"] = previous.get("modified") or timestamp_now
                final_entry["sequence"] = previous.get("sequence", 0)
            else:
                final_entry["created"] = previous.get("created") or timestamp_now
                final_entry["modified"] = timestamp_now
                final_entry["sequence"] = previous.get("sequence", 0) + 1
        else:
            final_entry["created"] = timestamp_now
            final_entry["modified"] = timestamp_now
            final_entry["sequence"] = 0

        final_entries.append(final_entry)

    final_entries.sort(key=lambda item: (item["startDate"], item["endDate"], item["id"]))
    return final_entries


def main() -> None:
    print("Starting public holiday merge process")

    os.makedirs(PUBLIC_HOLIDAYS_RESULT_DIR, exist_ok=True)

    raw_entries = load_json_file(RAW_PATH, default_fallback=[])
    overrides = load_json_file(OVERRIDE_PATH, default_fallback={"new": [], "modify": [], "remove": []})
    previous_data = load_json_file(RESULT_PATH, default_fallback={})

    previous_list: List[Dict[str, Any]]
    if isinstance(previous_data, dict):
        previous_list = previous_data.get("holidays", []) if isinstance(previous_data.get("holidays", []), list) else []
    elif isinstance(previous_data, list):
        previous_list = previous_data
    else:
        previous_list = []

    previous_memory = {
        item["id"]: item
        for item in previous_list
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    working_data: Dict[str, Dict[str, Any]] = {}
    for entry in raw_entries:
        if not isinstance(entry, dict) or not should_keep_entry(entry):
            continue

        working_entry = build_working_entry(entry)
        if not working_entry:
            continue

        working_data[working_entry["id"]] = working_entry

    apply_overrides(working_data, overrides if isinstance(overrides, dict) else {})

    final_entries = enrich_with_metadata(working_data, previous_memory)
    final_result = {"holidays": final_entries}

    with open(RESULT_PATH, "w", encoding="utf-8") as file_handle:
        json.dump(final_result, file_handle, ensure_ascii=False, indent=2)

    print(f"File saved: {RESULT_PATH} (Total: {len(final_entries)} entries)")


if __name__ == "__main__":
    main()