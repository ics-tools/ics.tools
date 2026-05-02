import json
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from config import (
    PUBLIC_HOLIDAYS_OVERRIDE_DIR,
    PUBLIC_HOLIDAYS_RAW_DIR,
    PUBLIC_HOLIDAYS_RESULT_DIR,
    STATE_NAMES,
)


def calculate_md5(name: str, date: str) -> str:
    """Generates a stable MD5 hash for the core content."""
    content = f"{name}|{date}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def get_now_iso() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


def load_json_file(filepath: str, default_fallback: Any) -> Any:
    """Safely loads a JSON file, returning a fallback if it doesn't exist."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_fallback


def extract_name(
    name_list: Optional[List[Dict[str, str]]], entry_id: str, state: str
) -> str:
    """
    Extracts the German text from the API name array.
    Issues warnings if German name is missing or no name exists at all.
    """
    if not name_list or not isinstance(name_list, list) or len(name_list) == 0:
        print(
            f"::warning title=Missing Name,file={state}.json::No name found for holiday {entry_id} in {state}. Using 'Unknown'."
        )
        return "Unknown"

    # Try to find the German name
    for n in name_list:
        text = n.get("text")
        if n.get("language") == "DE" and text:
            return text

    # Fallback to the first available name if German is missing
    fallback_name = name_list[0].get("text", "Unknown")
    print(
        f"::warning title=Missing German Name,file={state}.json::German name missing for {entry_id} in {state}. Falling back to: {fallback_name}"
    )

    return fallback_name


def apply_overrides(
    working_data: Dict[str, Dict[str, Any]], overrides: Dict[str, List[Dict[str, Any]]]
) -> None:
    """Applies REMOVE, MODIFY, and NEW overrides in-place to the working data."""

    for remove_id in overrides.get("remove", []):
        if remove_id in working_data:
            del working_data[remove_id]

    for mod in overrides.get("modify", []):
        m_id = mod.get("id")
        if m_id in working_data:
            if "name" in mod:
                working_data[m_id]["name"] = mod["name"]
            if "startDate" in mod:
                working_data[m_id]["date"] = mod["startDate"]

    for new_entry in overrides.get("new", []):
        n_id = new_entry.get("id")

        if n_id:
            working_data[n_id] = {
                "id": n_id,
                "name": new_entry.get("name"),
                "date": new_entry.get("startDate"),
            }
        else:
            print("::warning::New override entry is missing an 'id'. Skipping.")


def enrich_with_metadata(
    state_code: str,
    state_name: str,
    working_data: Dict[str, Dict[str, Any]],
    previous_memory: Dict[str, Dict[str, Any]]
) -> dict[str, Any]:
    """Compares current data with previous memory to generate sequence numbers and update timestamps."""
    final_entries = []
    timestamp_now = get_now_iso()

    for entry_id, data in working_data.items():
        current_md5 = calculate_md5(data["name"], data["date"])
        prev = previous_memory.get(entry_id)

        final_entry: Dict[str, Any] = {**data, "md5": current_md5}

        if prev:
            if prev.get("md5") == current_md5:
                # No changes detected
                final_entry.update(
                    {
                        "created": prev.get("created"),
                        "modified": prev.get("modified"),
                        "sequence": prev.get("sequence"),
                    }
                )
            else:
                # Change detected, bump sequence and modify timestamp
                print(f"  📝 Change detected: {data['name']} ({entry_id})")
                final_entry.update(
                    {
                        "created": prev.get("created"),
                        "modified": timestamp_now,
                        "sequence": prev.get("sequence", 0) + 1,
                    }
                )
        else:
            # Entirely new entry
            final_entry.update(
                {
                    "created": timestamp_now,
                    "modified": timestamp_now,
                    "sequence": 0,
                }
            )

        final_entries.append(final_entry)

    # Sort final list chronologically
    final_entries.sort(key=lambda x: x["date"])

    return {
        "$schema": "../../schema/public-holidays.schema.json",
        "metadata": {"state": state_name, "code": state_code},
        "holidays": final_entries,
    }


def process_state(state_code: str, state_name: str) -> None:
    """Handles the complete processing pipeline for a single state."""
    print(f"::group::Merging {state_name} ({state_code})")

    raw_path = os.path.join(PUBLIC_HOLIDAYS_RAW_DIR, f"{state_code}.json")
    override_path = os.path.join(PUBLIC_HOLIDAYS_OVERRIDE_DIR, f"{state_code}.json")
    result_path = os.path.join(PUBLIC_HOLIDAYS_RESULT_DIR, f"{state_code}.json")

    # 1. Load Data
    raw_entries = load_json_file(raw_path, default_fallback=[])
    overrides = load_json_file(
        override_path, default_fallback={"new": [], "modify": [], "remove": []}
    )

    prev_data = load_json_file(result_path, default_fallback=[])
    if isinstance(prev_data, dict):
        prev_list = prev_data.get("holidays", [])
    else:
        prev_list = prev_data

    previous_memory = {
        item["id"]: item for item in prev_list if isinstance(item, dict) and "id" in item
    }

    # 2. Build Base Data
    working_data = {}
    for entry in raw_entries:
        if entry.get("regionalScope") == "Local":
            continue

        entry_id = entry.get("id")
        working_data[entry_id] = {
            "id": entry_id,
            "name": extract_name(entry.get("name"), entry_id, state_code),
            "date": entry.get("startDate"),
        }

    # 3. Apply Overrides
    apply_overrides(working_data, overrides)

    # 4. Process Metadata & Hashes
    final_result = enrich_with_metadata(
        state_code, state_name, working_data, previous_memory
    )

    # 5. Save Result
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print(f"✅ Finished {state_name} ({state_code})")
    print("::endgroup::")


def main():
    os.makedirs(PUBLIC_HOLIDAYS_RESULT_DIR, exist_ok=True)
    print("Starting merge process with MD5 hashing")

    for state_code, state_name in STATE_NAMES.items():
        process_state(state_code, state_name)

    print("Merge process completed.")


if __name__ == "__main__":
    main()
