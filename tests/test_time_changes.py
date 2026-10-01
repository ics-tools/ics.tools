import sys
from datetime import date
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from time_change_utils import last_sunday


@pytest.mark.parametrize(
    ("year", "month", "expected"),
    [
        (2024, 3, date(2024, 3, 31)),
        (2025, 3, date(2025, 3, 30)),
        (2026, 3, date(2026, 3, 29)),
        (2024, 10, date(2024, 10, 27)),
        (2025, 10, date(2025, 10, 26)),
        (2026, 10, date(2026, 10, 25)),
    ],
)
def test_last_sunday(year, month, expected):
    assert last_sunday(year, month) == expected