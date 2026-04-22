import requests
import json
import os
import time
from datetime import datetime

# --- Configuration ---
BASE_URL = "https://openholidaysapi.org/PublicHolidays"
COUNTRY_CODE = "DE"
LANG = "DE" 
START_YEAR = 2020
END_YEAR = datetime.now().year + 2
OUTPUT_DIR = "data/public_holidays/raw"
SLEEP_INTERVAL = 0.5
# ----

SUBDIVISIONS = [
    "BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV", 
    "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH"
]

print("Starting public holiday fetch from OpenHolidays API")
print(f"Period: {START_YEAR} to {END_YEAR}")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

total_states = len(SUBDIVISIONS)

for index, state in enumerate(SUBDIVISIONS, start=1):
    all_holidays = []
    
    print(f"::group::Processing {state} ({index}/{total_states})")
    print(f"Starting request for {state}...")
    
    for year in range(START_YEAR, END_YEAR + 1):
        params = {
            "countryIsoCode": COUNTRY_CODE,
            "languageIsoCode": LANG,
            "subdivisionCode": f"{COUNTRY_CODE}-{state}",
            "validFrom": f"{year}-01-01",
            "validTo": f"{year}-12-31"
        }
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                all_holidays.extend(data)
                print(f"  ✅ {year}: {len(data)} holidays loaded.")
            
        except Exception as e:
            print(f"  ❌ Error for {state} in year {year}: {e}")

        # Short pause to avoid overloading the API
        time.sleep(SLEEP_INTERVAL)

    # Sort data by start date
    all_holidays.sort(key=lambda x: x.get('startDate', ''))

    file_path = os.path.join(OUTPUT_DIR, f"{state}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_holidays, f, ensure_ascii=False, indent=2)
    
    print(f"File saved: {file_path} (Total: {len(all_holidays)} entries)")
    print("::endgroup::")


print("✅ All states processed successfully.")
