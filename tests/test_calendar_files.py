import pytest
import os
from collections import defaultdict
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
    with open(path, 'rb') as f:
        try:
            cal = Calendar.from_ical(f.read())
        except Exception as e:
            pytest.fail(f"Failed to parse ICS file {path}: {e}")
    return cal, path


@pytest.fixture(params=find_ferien_ics_files())
def parsed_ferien_calendar(request):
    path = request.param
    with open(path, 'rb') as f:
        try:
            cal = Calendar.from_ical(f.read())
        except Exception as e:
            pytest.fail(f"Failed to parse ICS file {path}: {e}")
    return cal, path


def build_expected_calendar_name(ics_path: str) -> str:
    dirname = os.path.basename(os.path.dirname(ics_path))
    filename = os.path.splitext(os.path.basename(ics_path))[0]

    expected_name_part = filename.title()
    return f"{expected_name_part} {dirname}"

def test_calendar_name_matches_filename_with_suffix(parsed_calendar):
    cal, path = parsed_calendar

    cal_name = cal.get('NAME')
    x_wr_cal_name = cal.get('X-WR-CALNAME')

    assert cal_name is not None, f"Calendar name (NAME) is missing in {path}"
    assert x_wr_cal_name is not None, f"Calendar name (X-WR-CALNAME) is missing in {path}"

    expected_name = build_expected_calendar_name(path)
    assert cal_name == expected_name, f"Expected calendar name '{expected_name}', but found '{cal_name}' (NAME) in {path}"
    assert x_wr_cal_name == expected_name, f"Expected calendar name '{expected_name}', but found '{x_wr_cal_name}' (X-WR-CALNAME) in {path}"


def test_no_close_events_with_same_title_in_ferien_calendars(parsed_ferien_calendar):
    """Test that events with the same title have more than 1 day between end of one and start of next in Ferien calendars."""
    cal, path = parsed_ferien_calendar

    events_by_title = defaultdict(list)

    for component in cal.walk():
        if component.name == "VEVENT":
            summary = component.get('SUMMARY')
            dtstart = component.get('DTSTART')
            dtend = component.get('DTEND')

            if summary is not None and dtstart is not None:
                title = str(summary)

                start_date = dtstart.dt
                if hasattr(start_date, 'date'):
                    start_date = start_date.date()

                if dtend is not None:
                    end_date = dtend.dt
                    if hasattr(end_date, 'date'):
                        end_date = end_date.date()
                else:
                    end_date = start_date

                events_by_title[title].append({
                    'start': start_date,
                    'end': end_date
                })

    close_events = []

    for title, events in events_by_title.items():
        if len(events) > 1:
            sorted_events = sorted(events, key=lambda x: x['start'])

            for i in range(len(sorted_events) - 1):
                event1 = sorted_events[i]
                event2 = sorted_events[i + 1]

                end_date1 = event1['end']
                start_date2 = event2['start']

                if hasattr(end_date1, 'toordinal') and hasattr(start_date2, 'toordinal'):
                    days_diff = start_date2.toordinal() - end_date1.toordinal()
                else:
                    if hasattr(end_date1, 'date'):
                        end_date1 = end_date1.date()
                    if hasattr(start_date2, 'date'):
                        start_date2 = start_date2.date()
                    days_diff = (start_date2 - end_date1).days

                if 0 <= days_diff <= 1:
                    close_events.append({
                        'title': title,
                        'event1_start': event1['start'],
                        'event1_end': event1['end'],
                        'event2_start': event2['start'],
                        'event2_end': event2['end'],
                        'gap_days': days_diff
                    })

    if close_events:
        error_messages = []
        for event in close_events:
            error_messages.append(
                f"  '{event['title']}': Event 1 ({event['event1_start']} - {event['event1_end']}) "
                f"and Event 2 ({event['event2_start']} - {event['event2_end']}) "
                f"have only {event['gap_days']} days gap"
            )

        error_info = "\n".join(error_messages)
        pytest.fail(
            f"Events with same title found with 1 day or less gap in Ferien calendar {path}:\n{error_info}"
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