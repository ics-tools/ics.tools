from datetime import datetime

COUNTRY_CODE = "DE"
LANGUAGE_CODE = "DE"

FETCH_START_YEAR = 2020
FETCH_END_YEAR = datetime.now().year + 2
FETCH_SLEEP_SECONDS = 0.5

STATE_NAMES = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen",
}

STATE_CODES = list(STATE_NAMES.keys())

PUBLIC_HOLIDAYS_API_URL = "https://openholidaysapi.org/PublicHolidays"
SCHOOL_HOLIDAYS_API_URL = "https://openholidaysapi.org/SchoolHolidays"

PUBLIC_HOLIDAYS_RAW_DIR = "data/public_holidays/raw"
PUBLIC_HOLIDAYS_OVERRIDE_DIR = "data/public_holidays/override"
PUBLIC_HOLIDAYS_RESULT_DIR = "data/public_holidays/result"
PUBLIC_HOLIDAYS_ICS_DIR = "Feiertage"

SCHOOL_HOLIDAYS_RAW_DIR = "data/school_holidays/raw"
SCHOOL_HOLIDAYS_OVERRIDE_DIR = "data/school_holidays/override"
SCHOOL_HOLIDAYS_RESULT_DIR = "data/school_holidays/result"
SCHOOL_HOLIDAYS_ICS_DIR = "Ferien"

# Raw holiday entries carrying any of these tags are skipped during merge.
IGNORED_RAW_TAGS = ["Exception"]

# Website generation config
WEBSITE_BASE_URL = "https://ics.tools/"
WEBSITE_TEMPLATE_DIR = "website_template"
WEBSITE_RESULT_DIR = "website_result"
WEBSITE_TEMPLATE_FILE = "index_template.md"
WEBSITE_OUTPUT_FILE = "index.md"
WEBSITE_ICS_SOURCE_DIRS = [
    PUBLIC_HOLIDAYS_ICS_DIR,
    SCHOOL_HOLIDAYS_ICS_DIR,
]
WEBSITE_PLACEHOLDERS = {
    PUBLIC_HOLIDAYS_ICS_DIR: "[[feiertage-tree]]",
    SCHOOL_HOLIDAYS_ICS_DIR: "[[ferien-tree]]",
}


def subdivision_code(state_code: str) -> str:
    return f"{COUNTRY_CODE}-{state_code}"
