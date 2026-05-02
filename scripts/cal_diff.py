import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from icalendar import Calendar


def parse_ics_to_dict(filepath):
    """Liest eine ICS-Datei und gibt eine Liste von (start_date, end_date, summary) zurück."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            cal = Calendar.from_ical(f.read())
    except FileNotFoundError:
        print(f"Fehler: Datei '{filepath}' nicht gefunden.")
        sys.exit(1)

    events = []
    for component in cal.walk("VEVENT"):
        summary = str(component.get("summary", "Ohne Titel"))

        dtstart_prop = component.get("dtstart")
        if not dtstart_prop:
            continue
        dtstart = dtstart_prop.dt

        if isinstance(dtstart, datetime):
            dtstart = dtstart.date()

        dtend_prop = component.get("dtend")
        if dtend_prop:
            dtend = dtend_prop.dt
            if isinstance(dtend, datetime):
                dtend = dtend.date()

            if dtend > dtstart:
                inclusive_end = dtend - timedelta(days=1)
            else:
                inclusive_end = dtstart
        else:
            inclusive_end = dtstart

        events.append((dtstart, inclusive_end, summary))

    return events


def compare_calendars(file1, file2):
    """Vergleicht zwei Kalender und baut ein gruppiertes Dictionary auf."""
    events1 = parse_ics_to_dict(file1)
    events2 = parse_ics_to_dict(file2)

    diff_data = defaultdict(lambda: defaultdict(lambda: {"cal1": "---", "cal2": "---"}))

    for start_date, end_date, summary in events1:
        diff_data[start_date.year][(start_date, end_date)]["cal1"] = summary

    for start_date, end_date, summary in events2:
        diff_data[start_date.year][(start_date, end_date)]["cal2"] = summary

    return diff_data


def format_date(d):
    """Hilfsfunktion: Formatiert ein Datum in TT.MM.JJJJ"""
    return d.strftime("%d.%m.%Y")


def print_diff_table(diff_data):
    """Gibt das verglichene Dictionary als formatierte Tabelle aus."""
    print(
        f"{'Jahr':<4} | {'Zeitraum':<23} | {'Event in Kalender 1':<30} | {'Event in Kalender 2'}"
    )
    print("-" * 95)

    for year in sorted(diff_data.keys()):
        year_events = diff_data[year]

        for start_date, end_date in sorted(year_events.keys()):
            cal1_summary = year_events[(start_date, end_date)]["cal1"]
            cal2_summary = year_events[(start_date, end_date)]["cal2"]

            if cal1_summary == cal2_summary and cal1_summary != "---":
                continue

            if start_date == end_date:
                zeitraum = format_date(start_date)
            else:
                zeitraum = f"{format_date(start_date)} - {format_date(end_date)}"

            cal1_disp = (
                cal1_summary[:27] + "..." if len(cal1_summary) > 30 else cal1_summary
            )
            cal2_disp = (
                cal2_summary[:27] + "..." if len(cal2_summary) > 30 else cal2_summary
            )

            if year > 2026 or year < 2020:
                continue

            print(f"{year:<4} | {zeitraum:<23} | {cal1_disp:<30} | {cal2_disp}")


def compare_directories(dir1_path, dir2_path):
    """Vergleicht ICS-Dateien mit identischem Namen aus zwei Verzeichnissen."""
    path1 = Path(dir1_path)
    path2 = Path(dir2_path)

    if not path1.is_dir() or not path2.is_dir():
        print("Fehler: Einer der angegebenen Pfade ist kein gültiges Verzeichnis.")
        return

    files1 = {f.name: f for f in path1.glob("*.ics")}
    files2 = {f.name: f for f in path2.glob("*.ics")}

    all_filenames = sorted(set(files1.keys()).union(set(files2.keys())))

    for filename in all_filenames:
        if filename in files1 and filename in files2:
            print(f"\n\n{'='*95}")
            print(f" DATEI: {filename}")
            print(f"{'='*95}")

            try:
                diff = compare_calendars(files1[filename], files2[filename])
                print_diff_table(diff)
            except Exception as e:
                print(f"Fehler beim Vergleichen von {filename}: {e}")

        elif filename in files1:
            print(
                f"\n[INFO] Übersprungen: '{filename}' existiert nur in Ordner 1 ({dir1_path})"
            )
        elif filename in files2:
            print(
                f"\n[INFO] Übersprungen: '{filename}' existiert nur in Ordner 2 ({dir2_path})"
            )


if __name__ == "__main__":
    ordner_1 = "old/Ferien"
    ordner_2 = "Ferien"

    print(
        f"Starte Verzeichnis-Vergleich:\nOrdner 1: {ordner_1}\nOrdner 2: {ordner_2}\n"
    )

    compare_directories(ordner_1, ordner_2)
