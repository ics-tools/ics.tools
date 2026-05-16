import pytest
import os
from datetime import datetime, timedelta

import requests
from icalendar import Calendar

ICAL_VALIDATOR_URL = "https://icalendar.org/validator.html?json=1"

def find_ics_files(base_path='./'):
    ics_files = []
    for root, _, files in os.walk(base_path):
        path_parts = set(os.path.normpath(root).split(os.sep))
        if path_parts.intersection({'Feiertage', 'Ferien'}):
            for file in files:
                if file.endswith('.ics'):
                    ics_files.append(os.path.join(root, file))
    return ics_files


def find_ferien_ics_files(base_path='./'):
    """Find only ICS files in 'Ferien' directories."""
    ics_files = []
    for root, _, files in os.walk(base_path):
        path_parts = set(os.path.normpath(root).split(os.sep))
        if 'Ferien' in path_parts:
            for file in files:
                if file.endswith('.ics'):
                    ics_files.append(os.path.join(root, file))
    return ics_files


@pytest.fixture(params=find_ics_files())
def parsed_calendar(request):
    path = request.param
    with open(path, "r", encoding="utf-8") as f:
        try:
            cal = Calendar.from_ical(f.read())
        except Exception as e:
            pytest.fail(f"Failed to parse ICS file {path}: {e}")
    return cal, path


@pytest.fixture(params=find_ferien_ics_files())
def parsed_ferien_calendar(request):
    path = request.param
    with open(path, "r", encoding="utf-8") as f:
        try:
            cal = Calendar.from_ical(f.read())
        except Exception as e:
            pytest.fail(f"Failed to parse ICS file {path}: {e}")
    return cal, path


def build_expected_calendar_name(ics_path: str) -> str:
    dirname = os.path.basename(os.path.dirname(ics_path))
    filename = os.path.splitext(os.path.basename(ics_path))[0]

    match dirname:
        case "Ferien":
            category_name = "Schulferien"
        case _:
            category_name = dirname

    expected_name_part = filename.title()
    
    if filename == "bundesweit" and dirname == "Feiertage":
        expected_name_part = "Bundesweite"
    
    return f"{expected_name_part} {category_name}"


def iter_event_days(component):
    dtstart_prop = component.get("dtstart")
    if not dtstart_prop:
        return []

    dtstart = dtstart_prop.dt
    dtstart_date = dtstart.date() if isinstance(dtstart, datetime) else dtstart

    dtend_prop = component.get("dtend")
    if not dtend_prop:
        return [dtstart_date]

    dtend = dtend_prop.dt

    if isinstance(dtend, datetime):
        end_date = dtend.date() - timedelta(days=1) if dtend.time() == datetime.min.time() else dtend.date()
    else:
        end_date = dtend - timedelta(days=1)

    if end_date < dtstart_date:
        end_date = dtstart_date

    return [dtstart_date + timedelta(days=offset) for offset in range((end_date - dtstart_date).days + 1)]


def get_event_period(component):
    dtstart_prop = component.get("dtstart")
    if not dtstart_prop:
        return None

    dtstart = dtstart_prop.dt
    start_date = dtstart.date() if isinstance(dtstart, datetime) else dtstart

    dtend_prop = component.get("dtend")
    if not dtend_prop:
        return start_date, start_date

    dtend = dtend_prop.dt
    if isinstance(dtend, datetime):
        end_date = dtend.date() - timedelta(days=1) if dtend.time() == datetime.min.time() else dtend.date()
    else:
        end_date = dtend - timedelta(days=1)

    if end_date < start_date:
        end_date = start_date

    return start_date, end_date

def test_calendar_name_matches_filename_with_suffix(parsed_calendar):
    cal, path = parsed_calendar

    cal_name = cal.get('NAME')
    x_wr_cal_name = cal.get('X-WR-CALNAME')

    assert cal_name is not None, f"Calendar name (NAME) is missing in {path}"
    assert x_wr_cal_name is not None, f"Calendar name (X-WR-CALNAME) is missing in {path}"

    expected_name = build_expected_calendar_name(path)
    assert cal_name == expected_name, f"Expected calendar name '{expected_name}', but found '{cal_name}' (NAME) in {path}"
    assert x_wr_cal_name == expected_name, f"Expected calendar name '{expected_name}', but found '{x_wr_cal_name}' (X-WR-CALNAME) in {path}"


def test_no_overlapping_event_periods(parsed_calendar):
    cal, path = parsed_calendar

    events = []

    for component in cal.walk("VEVENT"):
        summary = str(component.get("summary", "Ohne Titel"))
        event_period = get_event_period(component)
        if event_period is None:
            continue

        start_date, end_date = event_period
        events.append((summary, start_date, end_date))

    conflicts = []
    for index, (summary_a, start_a, end_a) in enumerate(events):
        for summary_b, start_b, end_b in events[index + 1 :]:
            overlap_start = max(start_a, start_b)
            overlap_end = min(end_a, end_b)
            if overlap_start <= overlap_end:
                conflicts.append((summary_a, start_a, end_a, summary_b, start_b, end_b, overlap_start, overlap_end))

    assert not conflicts, (
        f"Found overlapping event periods in {path} ({len(conflicts)} pairs):\n"
        + "\n".join(
            f"- {summary_a} [{start_a} -> {end_a}] <-> {summary_b} [{start_b} -> {end_b}] | overlap {overlap_start}..{overlap_end}"
            for summary_a, start_a, end_a, summary_b, start_b, end_b, overlap_start, overlap_end in conflicts[:25]
        )
        + (f"\n... and {len(conflicts) - 25} more" if len(conflicts) > 25 else "")
    )


@pytest.mark.parametrize("ics_path", find_ics_files())
def test_icalendar_org_validator(ics_path):
    with open(ics_path, 'rb') as f:
        files = {
            "jform[task]": (None, "validate"),
            "jform[ical_file]": (os.path.basename(ics_path), f, "text/calendar"),
        }
        response = requests.post(ICAL_VALIDATOR_URL, files=files)
        response.raise_for_status()
        data = response.json()

    errors = data.get("totals", {}).get("errors", 0)
    warnings = data.get("totals", {}).get("warnings", 0)

    if errors > 0:
        messages = "\n".join(err["message"] for err in data.get("errors", []))
        pytest.fail(f"Validation errors in {ics_path}:\n{messages}")

    if warnings > 0:
        messages = "\n".join(warn["message"] for warn in data.get("warnings", []))
        pytest.skip(f"Validation warnings in {ics_path}:\n{messages}")
