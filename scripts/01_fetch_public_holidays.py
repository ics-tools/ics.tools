# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
from datetime import date

import requests
from config import (
    COUNTRY_CODE,
    FETCH_END_YEAR,
    FETCH_START_YEAR,
    LANGUAGE_CODE,
    PUBLIC_HOLIDAYS_API_URL,
    PUBLIC_HOLIDAYS_RAW_DIR,
)


def build_date_chunks(start_year: int, end_year: int) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []

    for year in range(start_year, end_year + 1):
        chunks.append((date(year, 1, 1), date(year, 12, 31)))

    return chunks


def main() -> None:
    print("Starting public holiday fetch from OpenHolidays API")
    print(f"Period: {FETCH_START_YEAR} to {FETCH_END_YEAR}")

    os.makedirs(PUBLIC_HOLIDAYS_RAW_DIR, exist_ok=True)

    all_holidays = []

    chunks = build_date_chunks(FETCH_START_YEAR, FETCH_END_YEAR)
    print(f"Split into {len(chunks)} request window(s)")

    for index, (chunk_start, chunk_end) in enumerate(chunks, start=1):
        print(f"Request {index}/{len(chunks)}: {chunk_start} to {chunk_end}")

        params = {
            "countryIsoCode": COUNTRY_CODE,
            "languageIsoCode": LANGUAGE_CODE,
            "validFrom": chunk_start.isoformat(),
            "validTo": chunk_end.isoformat(),
        }

        response = requests.get(PUBLIC_HOLIDAYS_API_URL, params=params, timeout=15)

        if response.status_code != 200:
            raise RuntimeError(
                f"Public holiday request failed with status {response.status_code}: {response.text}"
            )

        data = response.json()
        if isinstance(data, list):
            all_holidays.extend(data)

    all_holidays.sort(key=lambda item: item.get("startDate", ""))

    output_path = os.path.join(PUBLIC_HOLIDAYS_RAW_DIR, "de.json")

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(all_holidays, output_file, ensure_ascii=False, indent=2)

    print(f"File saved: {output_path} (Total: {len(all_holidays)} entries)")


if __name__ == "__main__":
    main()