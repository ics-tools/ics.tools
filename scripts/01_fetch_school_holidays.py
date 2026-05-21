# SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import time

import requests
from config import (
    COUNTRY_CODE,
    FETCH_END_YEAR,
    FETCH_SLEEP_SECONDS,
    FETCH_START_YEAR,
    LANGUAGE_CODE,
    SCHOOL_HOLIDAYS_API_URL,
    SCHOOL_HOLIDAYS_RAW_DIR,
    STATE_CODES,
    subdivision_code,
)

print("Starting school holiday fetch from OpenHolidays API")
print(f"Period: {FETCH_START_YEAR} to {FETCH_END_YEAR}")

os.makedirs(SCHOOL_HOLIDAYS_RAW_DIR, exist_ok=True)

total_states = len(STATE_CODES)

for index, state in enumerate(STATE_CODES, start=1):
    all_holidays = []

    print(f"::group::Processing {state} ({index}/{total_states})")
    print(f"Starting request for {state}...")

    for year in range(FETCH_START_YEAR, FETCH_END_YEAR + 1):
        params = {
            "countryIsoCode": COUNTRY_CODE,
            "languageIsoCode": LANGUAGE_CODE,
            "subdivisionCode": subdivision_code(state),
            "validFrom": f"{year}-01-01",
            "validTo": f"{year}-12-31",
        }

        try:
            response = requests.get(SCHOOL_HOLIDAYS_API_URL, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                all_holidays.extend(data)
                print(f"  {year}: {len(data)} school holidays loaded.")

        except Exception as exc:
            print(f"  Error for {state} in year {year}: {exc}")

        time.sleep(FETCH_SLEEP_SECONDS)

    all_holidays.sort(key=lambda x: x.get("startDate", ""))

    file_path = os.path.join(SCHOOL_HOLIDAYS_RAW_DIR, f"{state}.json")
    with open(file_path, "w", encoding="utf-8") as output_file:
        json.dump(all_holidays, output_file, ensure_ascii=False, indent=2)

    print(f"File saved: {file_path} (Total: {len(all_holidays)} entries)")
    print("::endgroup::")

print("All states processed successfully.")
