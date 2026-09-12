"""
Regex extraction: numbers, units, dates, phone numbers, emails, batch codes.

Deliberately tolerant of common OCR misreads seen in real test photos
(e.g. 'MFD' printed but read as 'HFD' -- M/H confusion in dot-matrix print).
Exact-match assumptions break on real OCR text; these patterns don't.
"""

import re
from typing import List, Optional, Tuple

from app.classification.keywords import _fuzzy_word_in

# --- MRP -------------------------------------------------------------------

# Amount only -- the 'MRP' keyword itself is checked separately (with fuzzy
# tolerance) below, since a single misread character turns 'MRP' into 'MRE'
# or similar, and requiring the literal string in one combined regex breaks
# on exactly that kind of noise.
AMOUNT_PATTERN = re.compile(
    r"[:\-]?\s*(?:RS\.?|₹|INR)?\s*([\d,]+(?:\.\d{1,2})?)\s*/?"
)

TAX_INCLUDED_PATTERN = re.compile(r"incl(?:usive|\.)?\s*(?:of)?\s*(?:all)?\s*tax", re.IGNORECASE)


def find_mrp(text: str) -> Optional[Tuple[float, bool]]:
    """Return (value, tax_included) if this line looks like an MRP declaration.

    Requires a fuzzy match on 'MRP' (tolerating 1-character OCR noise) AND a
    numeric amount somewhere in the same line -- not just a bare number,
    since plenty of other fields (dates, batch codes) also contain digits.
    """
    if not _fuzzy_word_in(text, "mrp", max_distance=1):
        return None
    match = AMOUNT_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    tax_included = bool(TAX_INCLUDED_PATTERN.search(text)) or None
    return value, tax_included


# --- Net quantity ------------------------------------------------------------

UNIT_ALIASES = {
    "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
    "kg": "kg", "kgs": "kg",
    "ml": "ml", "mls": "ml",
    "l": "l", "ltr": "l", "ltrs": "l", "litre": "l", "litres": "l", "liter": "l", "liters": "l",
    "mg": "mg",
    "n": "n", "no": "n", "nos": "n", "pcs": "n", "pieces": "n", "count": "n",
}

QUANTITY_TYPE_BY_UNIT = {
    "g": "mass", "kg": "mass", "mg": "mass",
    "ml": "volume", "l": "volume",
    "n": "number",
}

NET_QTY_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|kg|kgs|ml|mls|l|ltr|ltrs|litre|litres|liter|liters|mg)\b",
    re.IGNORECASE,
)


def find_net_quantity(text: str) -> Optional[dict]:
    """Return {rawValue, value, unit, quantityType, normalizedValue, normalizedUnit}."""
    match = NET_QTY_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(1))
    raw_unit = match.group(2).lower()
    unit = UNIT_ALIASES.get(raw_unit, raw_unit)
    quantity_type = QUANTITY_TYPE_BY_UNIT.get(unit, "unknown")

    normalized_value, normalized_unit = value, unit
    if unit == "kg":
        normalized_value, normalized_unit = value * 1000, "g"
    elif unit == "l":
        normalized_value, normalized_unit = value * 1000, "ml"

    return {
        "rawValue": match.group(0),
        "value": value,
        "unit": unit,
        "quantityType": quantity_type,
        "normalizedValue": normalized_value,
        "normalizedUnit": normalized_unit,
    }


# --- Dates -------------------------------------------------------------------

# Matches DD/MM/YYYY, DD/MM/YY, or MM/YYYY -- '-' or '.' also accepted as separators.
DATE_PATTERN = re.compile(
    r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b|\b(\d{1,2})[/\-.](\d{4})\b"
)


def find_date(text: str) -> Optional[dict]:
    """Return {raw, day, month, year} for the first date-like pattern found."""
    match = DATE_PATTERN.search(text)
    if not match:
        return None

    if match.group(1):  # DD/MM/YYYY or DD/MM/YY
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if year < 100:
            year += 2000
    else:  # MM/YYYY
        day = None
        month, year = int(match.group(4)), int(match.group(5))

    if not (1 <= month <= 12):
        return None  # not actually a date (e.g. a barcode fragment)

    return {"raw": match.group(0), "day": day, "month": month, "year": year}


# --- Contact details -----------------------------------------------------------

# Indian phone numbers: +91 prefix optional, 10 digits, optionally split into groups.
PHONE_PATTERN = re.compile(r"(?:\+?91[-\s]?)?\d{5}[-\s]?\d{5}\b")

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

PIN_CODE_PATTERN = re.compile(r"\b(\d{6})\b")


def find_phones(text: str) -> List[str]:
    return [m.group(0).strip() for m in PHONE_PATTERN.finditer(text)]


def find_email(text: str) -> Optional[str]:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def find_pin_code(text: str) -> Optional[str]:
    match = PIN_CODE_PATTERN.search(text)
    return match.group(1) if match else None


# --- Batch / lot number --------------------------------------------------------

BATCH_PATTERN = re.compile(r"B\.?\s*NO\s*[:\-.]?\s*([A-Z0-9]+)", re.IGNORECASE)


def find_batch_number(text: str) -> Optional[str]:
    match = BATCH_PATTERN.search(text)
    return match.group(1) if match else None
