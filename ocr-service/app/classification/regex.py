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

# Guards against exactly the failure seen on a real label: a line-merge
# artifact combined "MRPZ" (garbled MRP) with ":180 ml" (a NET VOLUME from a
# different label a few pixels away), and naive "first number in the line"
# extraction grabbed 180 as the price -- a wrong value, not just a missing
# one. If the number found is immediately followed by a recognized unit,
# it's a quantity, not a price, regardless of what keyword shares the line.
UNIT_SUFFIX_PATTERN = re.compile(
    r"^\s*(g|gm|gms|gram|grams|kg|kgs|ml|mls|l|ltr|ltrs|litre|litres|liter|liters|mg)\b",
    re.IGNORECASE,
)

TAX_INCLUDED_PATTERN = re.compile(r"incl(?:usive|\.)?\s*(?:of)?\s*(?:all)?\s*tax", re.IGNORECASE)


def find_bare_amount(text: str) -> Optional[float]:
    """Find a monetary amount with NO keyword requirement -- for windowed
    search on lines near a confirmed 'MRP' keyword line, when the amount
    itself ended up on a different (unmerged) line."""
    for match in AMOUNT_PATTERN.finditer(text):
        remainder = text[match.end():]
        if UNIT_SUFFIX_PATTERN.match(remainder):
            continue
        return float(match.group(1).replace(",", ""))
    return None


def is_mrp_line(text: str) -> bool:
    """True if this line looks like it's introducing an MRP, regardless of
    whether the amount is also present on this same line."""
    return _fuzzy_word_in(text, "mrp", max_distance=1)


def find_mrp(text: str) -> Optional[Tuple[float, bool]]:
    """Return (value, tax_included) if this line looks like an MRP declaration.

    Requires a fuzzy match on 'MRP' (tolerating 1-character OCR noise) AND a
    numeric amount somewhere in the same line -- not just a bare number,
    since plenty of other fields (dates, batch codes) also contain digits.
    Scans ALL number candidates on the line and skips any immediately
    followed by a unit (g/ml/kg/...) -- that's a quantity, not a price.
    """
    if not _fuzzy_word_in(text, "mrp", max_distance=1):
        return None
    for match in AMOUNT_PATTERN.finditer(text):
        remainder = text[match.end():]
        if UNIT_SUFFIX_PATTERN.match(remainder):
            continue  # this number is a quantity (e.g. "180 ml"), not the price
        value = float(match.group(1).replace(",", ""))
        tax_included = bool(TAX_INCLUDED_PATTERN.search(text)) or None
        return value, tax_included
    return None


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

MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# "15 JUL 2024" / "15 July 2024" -- the format used across most real Indian
# packaged-goods labels (Haldiram's, Nandini, Bisleri, Everest, Dove, Tata
# Tea all use this, none use numeric DD/MM/YYYY). Matched separately from
# DATE_PATTERN since month names need a name->number lookup, not int().
DATE_PATTERN_MONTH_NAME = re.compile(
    r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b"
)


def find_date(text: str) -> Optional[dict]:
    """Return {raw, day, month, year} for the first date-like pattern found.
    Tries numeric formats (DD/MM/YYYY, MM/YYYY) first, then 'DD MON YYYY'."""
    match = DATE_PATTERN.search(text)
    if match:
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

    month_name_match = DATE_PATTERN_MONTH_NAME.search(text)
    if month_name_match:
        day = int(month_name_match.group(1))
        month_key = month_name_match.group(2).lower()[:3]
        year = int(month_name_match.group(3))
        month = MONTH_NAMES.get(month_key)
        if month is None or not (1 <= day <= 31):
            return None  # e.g. matched something that isn't actually a month name
        return {"raw": month_name_match.group(0), "day": day, "month": month, "year": year}

    return None


# --- Contact details -----------------------------------------------------------

# Indian phone numbers: +91 prefix optional, 10 digits, optionally split into groups.
# Indian phone numbers: +91 prefix optional, 10 digits, optionally split into
# groups. Uses lookbehind/lookahead (not \b) on BOTH ends: a plain \b only
# guards the end of the match, so a 10-digit substring embedded inside a
# longer, unbroken digit run (e.g. a batch/lot code like "11221331000187")
# could still match if it happened to end at a real word boundary. Requiring
# "not preceded/followed by another digit" on both sides rejects that
# regardless of where the boundary happens to fall.
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?\d{5}[-\s]?\d{5}(?!\d)")

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

BATCH_PATTERN = re.compile(r"(?:BATCH\s*NO\.?|B\.?\s*NO)\s*[:\-.]?\s*([A-Z0-9]+)", re.IGNORECASE)


BATCH_KEYWORD_PATTERN = re.compile(r"BATCH\s*NO\.?|B\.?\s*NO", re.IGNORECASE)
BATCH_VALUE_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]{3,})\b")  # e.g. AB0724, T0724, B0724, D0724


def is_batch_line(text: str) -> bool:
    """True if this line looks like it's introducing a batch number,
    regardless of whether the code itself is also present on this line."""
    return bool(BATCH_KEYWORD_PATTERN.search(text))


def find_bare_batch_value(text: str) -> Optional[str]:
    """Find a batch-code-shaped token with NO keyword requirement -- for
    windowed search on lines near a confirmed batch-keyword line, when the
    code itself ended up on a different (unmerged) line."""
    match = BATCH_VALUE_PATTERN.search(text)
    return match.group(1) if match else None


def find_batch_number(text: str) -> Optional[str]:
    match = BATCH_PATTERN.search(text)
    return match.group(1) if match else None
