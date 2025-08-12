import pytest
import os
from icalendar import Calendar

def find_ics_files(base_path='./'):
    ics_files = []
    for root, _, files in os.walk(base_path):
        path_parts = set(os.path.normpath(root).split(os.sep))
        if path_parts.intersection({'Feiertage', 'Ferien'}):
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
