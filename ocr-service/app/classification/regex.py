"""
Regex extraction: numbers, units, dates, phone numbers, emails, batch codes.

Deliberately tolerant of common OCR misreads seen in real test photos
(e.g. 'MFD' printed but read as 'HFD' -- M/H confusion in dot-matrix print).
Exact-match assumptions break on real OCR text; these patterns don't.
"""

import re
from typing import List, Optional, Tuple

from app.classification.keywords import _fuzzy_word_in, _levenshtein

# --- MRP -------------------------------------------------------------------

# Amount only -- the 'MRP' keyword itself is checked separately (with fuzzy
# tolerance) below, since a single misread character turns 'MRP' into 'MRE'
# or similar, and requiring the literal string in one combined regex breaks
# on exactly that kind of noise.
AMOUNT_PATTERN = re.compile(
    r"[:\-]?\s*(?:RS\.?|₹|INR)?\s*(\d[\d,]*(?:\.\d{1,2})?)\s*/?"
)

# Guards against exactly the failure seen on a real label: a line-merge
# artifact combined "MRPZ" (garbled MRP) with ":180 ml" (a NET VOLUME from a
# different label a few pixels away), and naive "first number in the line"
# extraction grabbed 180 as the price -- a wrong value, not just a missing
# one. If the number found is immediately followed by a recognized unit,
# it's a quantity, not a price, regardless of what keyword shares the line.
UNIT_SUFFIX_PATTERN = re.compile(
    r"^\s*(g|gm|gms|gram|grams|kg|kgs|ml|mls|l|ltr|ltrs|litre|litres|liter|liters|mg|n|no|nos|pcs|pieces|piece|count|units?|u|cm|mm|m|mtr|in|kcal|cal|kj)\b",
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
        raw_num = match.group(1).replace(",", "").rstrip(".")
        if not raw_num:
            continue
        try:
            return float(raw_num)
        except ValueError:
            continue
    return None


MRP_TOKEN_PATTERN = re.compile(r"[A-Za-z]+")


def _mrp_keyword_end_index(text: str) -> Optional[int]:
    """Find the end index of the fuzzy-matched 'mrp' keyword TOKEN, or None.

    Length guard: only words >= 3 characters are considered. A 2-letter word
    (e.g. 'MP' from 'SUPERIOR MP ATTA') can only reach 'MRP' via a deletion
    edit, which is not an OCR-noise pattern -- OCR misreads substitute or
    occasionally insert characters, they do not silently drop them. Without
    this guard, 'MP' would match 'MRP' (edit distance 1, length diff 1),
    triggering a false windowed search that grabs an unrelated number as
    the price (observed: Survey No. 77 from the manufacturer's address).
    """
    for m in MRP_TOKEN_PATTERN.finditer(text):
        word = m.group(0)
        # Reject words shorter than 'mrp' (3 chars): deletion-only edits are
        # not OCR noise. Only same-length (substitution) or longer (insertion).
        if len(word) < 3:
            continue
        if len(word) - 3 <= 1 and _levenshtein(word.lower(), "mrp") <= 1:
            return m.end()
    return None


def is_mrp_line(text: str) -> bool:
    """True if this line looks like it's introducing an MRP, regardless of
    whether the amount is also present on this same line."""
    return _mrp_keyword_end_index(text) is not None


def find_mrp(text: str) -> Optional[Tuple[float, bool]]:
    """Return (value, tax_included) if this line looks like an MRP declaration.

    Requires a fuzzy match on 'MRP' (tolerating 1-character OCR noise) AND a
    numeric amount somewhere in the same line -- not just a bare number,
    since plenty of other fields (dates, batch codes) also contain digits.
    Scans ALL number candidates on the line and skips any immediately
    followed by a unit (g/ml/kg/...) -- that's a quantity, not a price.

    Also rejects a digit glued DIRECTLY onto the keyword with zero
    separator (e.g. OCR-garbled "MRP7") -- real labels always have some
    gap (space, colon, currency symbol) between the label and its value;
    a digit fused onto the letters is almost always a stray OCR artifact,
    not an actual price.
    """
    keyword_end = _mrp_keyword_end_index(text)
    if keyword_end is None:
        return None
    if keyword_end < len(text) and text[keyword_end].isdigit():
        return None
    for match in AMOUNT_PATTERN.finditer(text):
        remainder = text[match.end():]
        if UNIT_SUFFIX_PATTERN.match(remainder):
            continue  # this number is a quantity (e.g. "180 ml"), not the price
        raw_num = match.group(1).replace(",", "").rstrip(".")
        if not raw_num:
            continue
        try:
            value = float(raw_num)
        except ValueError:
            continue
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
    "n": "n", "no": "n", "nos": "n", "pcs": "n", "pieces": "n", "piece": "n", "count": "n",
    "units": "n", "unit": "n", "u": "n",
}

QUANTITY_TYPE_BY_UNIT = {
    "g": "mass", "kg": "mass", "mg": "mass",
    "ml": "volume", "l": "volume",
    "n": "number",
}

NET_QTY_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|kg|kgs|ml|mls|l|ltr|ltrs|litre|litres|liter|liters|mg|n|no|nos|pcs|pieces|piece|count|units?|u)\b",
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


# --- Dimensions --------------------------------------------------------------

DIMENSION_UNITS = r"(?:cm|mm|m|mtr|mtrs|meter|meters|in|inch|inches)"

DIMENSION_UNIT_NORM = {
    "cm": "cm", "mm": "mm", "m": "m", "mtr": "m", "mtrs": "m", "meter": "m", "meters": "m",
    "in": "in", "inch": "in", "inches": "in",
}

MULTI_DIM_3_PATTERN = re.compile(
    rf"(\d+(?:\.\d+)?)\s*({DIMENSION_UNITS})?\s*[xX×]\s*(\d+(?:\.\d+)?)\s*({DIMENSION_UNITS})?\s*[xX×]\s*(\d+(?:\.\d+)?)\s*({DIMENSION_UNITS})\b",
    re.IGNORECASE,
)

MULTI_DIM_2_PATTERN = re.compile(
    rf"(\d+(?:\.\d+)?)\s*({DIMENSION_UNITS})?\s*[xX×]\s*(\d+(?:\.\d+)?)\s*({DIMENSION_UNITS})\b",
    re.IGNORECASE,
)

SINGLE_LABELED_DIM_PATTERN = re.compile(
    rf"\b(length|width|height|depth|breadth|size|dim|dimension|l|w|h|d|b)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*({DIMENSION_UNITS})\b",
    re.IGNORECASE,
)

DIMENSION_KEYWORD_PATTERN = re.compile(
    r"\b(?:dimensions?|size|measurement|dim)\b",
    re.IGNORECASE,
)


def is_dimension_line(text: str) -> bool:
    """True if text introduces a dimension declaration."""
    return bool(DIMENSION_KEYWORD_PATTERN.search(text))


def find_dimensions(text: str) -> List[dict]:
    """Return a list of dimension dicts: [{'label': str, 'value': float, 'unit': str}, ...]."""
    m3 = MULTI_DIM_3_PATTERN.search(text)
    if m3:
        fallback_unit = DIMENSION_UNIT_NORM.get(m3.group(6).lower(), m3.group(6).lower())
        u1 = DIMENSION_UNIT_NORM.get((m3.group(2) or "").lower(), fallback_unit)
        u2 = DIMENSION_UNIT_NORM.get((m3.group(4) or "").lower(), fallback_unit)
        u3 = fallback_unit
        return [
            {"label": "length", "value": float(m3.group(1)), "unit": u1},
            {"label": "width", "value": float(m3.group(3)), "unit": u2},
            {"label": "height", "value": float(m3.group(5)), "unit": u3},
        ]

    m2 = MULTI_DIM_2_PATTERN.search(text)
    if m2:
        fallback_unit = DIMENSION_UNIT_NORM.get(m2.group(4).lower(), m2.group(4).lower())
        u1 = DIMENSION_UNIT_NORM.get((m2.group(2) or "").lower(), fallback_unit)
        u2 = fallback_unit
        return [
            {"label": "length", "value": float(m2.group(1)), "unit": u1},
            {"label": "width", "value": float(m2.group(3)), "unit": u2},
        ]

    labeled_matches = list(SINGLE_LABELED_DIM_PATTERN.finditer(text))
    if labeled_matches:
        results = []
        label_map = {
            "l": "length", "w": "width", "h": "height", "d": "depth", "b": "breadth",
            "dim": "dimension", "dimensions": "dimension",
        }
        for lm in labeled_matches:
            raw_label = lm.group(1).lower()
            label = label_map.get(raw_label, raw_label)
            val = float(lm.group(2))
            unit = DIMENSION_UNIT_NORM.get(lm.group(3).lower(), lm.group(3).lower())
            results.append({"label": label, "value": val, "unit": unit})
        return results

    return []


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

# Indian phone numbers -- three distinct formats seen on real labels:
#
# 1. Mobile / 10-digit landline in 5+5 grouping (+91 prefix optional):
#    e.g. "+91 98444 88117", "98444 87302"
# 2. Toll-free 11-digit (1800 / 1860 / 1900 + 7 digits in any grouping):
#    e.g. "1800 121 1007", "1800 10 22 221", "1800 345 1720", "1800 425 8030"
#    All four are real consumer-care numbers from real labels in the test set.
# 3. +91-prefixed STD landline (area code 2-4 digits + local 6-8 digits):
#    e.g. "+91-120-2400286" (Haldiram's Noida office, STD 120)
#
# Uses lookbehind/lookahead on BOTH ends so a digit run embedded inside a
# longer unbroken run (batch codes, barcodes) is never partially matched.
PHONE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:"
    # Branch 1: mobile / 10-digit (5+5, +91 optional)  -- existing
    r"(?:\+?91[-\s]?)?\d{5}[-\s]?\d{5}"
    r"|"
    # Branch 2: toll-free 10/11-digit (1800/1860/1900 + 6 or 7 digits, any grouping).
    # (?:[-\s]?\d){6,7} matches the 6 or 7-digit body as individual digit steps with
    # optional separator between each, handling formats like:
    #   4+3+3  ("1800 222 001"),  4+3+4  ("1800 121 1007"),  4+7   ("18001211007")
    #   4+2+2+3 ("1800 10 22 221"), 4+3+4 ("1800 345 1720")
    r"1[89]\d{2}(?:[-\s]?\d){6,7}"
    r"|"
    # Branch 3: +91-prefixed STD landline (mandatory + or 91 prefix so bare
    # area-code numbers elsewhere don't false-positive).
    # Area code 2-4 digits, local number 6-8 digits, hyphen/space separator.
    r"\+?91[-\s]\d{2,4}[-\s]\d{6,8}"
    r")"
    r"(?!\d)"
)

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Matches either 6 consecutive digits OR the common Indian spaced format
# "NNN NNN" (e.g. "560 029" for Bengaluru -- both forms appear on real labels).
# Used as an address-accumulation stop signal in _classify_party_blocks:
# the party block ends when we see a PIN code line, so detecting the spaced
# form prevents the accumulator from overshooting into the FSSAI/consumer-care
# block that follows the address.
PIN_CODE_PATTERN = re.compile(r"\b(\d{6})\b|\b(\d{3})\s(\d{3})\b")


def find_phones(text: str) -> List[str]:
    return [m.group(0).strip() for m in PHONE_PATTERN.finditer(text)]


def find_email(text: str) -> Optional[str]:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def find_pin_code(text: str) -> Optional[str]:
    """Return a 6-digit PIN code string if found, else None.

    Matches both the compact form ('440016') and the common spaced 3+3
    form seen on real labels ('560 029', '249 403') -- the spaced form is
    returned without the internal space so callers always get 6 clean digits.
    """
    match = PIN_CODE_PATTERN.search(text)
    if not match:
        return None
    if match.group(1):          # 6 consecutive digits
        return match.group(1)
    return match.group(2) + match.group(3)  # spaced 3+3, normalised


# --- Batch / lot number --------------------------------------------------------

BATCH_PATTERN = re.compile(r"(?:BATCH\s*NO\.?|B\.?\s*NO)\s*[:\-.]?\s*([A-Z0-9]+)", re.IGNORECASE)


BATCH_KEYWORD_PATTERN = re.compile(r"BATCH\s*NO\.?|B\.?\s*NO", re.IGNORECASE)

# A bare batch value found on a neighboring line (without the 'Batch No' keyword)
# MUST contain at least one digit and at least one letter (e.g. A4G0724, B0724, AB0724,
# T0724, MNGMARDYI14, SB0824, BS2024G). This prevents plain all-caps dictionary words
# (e.g. 'ATTA', 'WHEAT', 'FLOUR', 'SELECT', 'BEST', 'PURE') from being misidentified as batch codes.
BATCH_VALUE_PATTERN = re.compile(r"\b(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*\d)([A-Z0-9]{3,20})\b", re.IGNORECASE)


def is_batch_line(text: str) -> bool:
    """True if this line looks like it's introducing a batch number,
    regardless of whether the code itself is also present on this line."""
    return bool(BATCH_KEYWORD_PATTERN.search(text))


def find_bare_batch_value(text: str) -> Optional[str]:
    """Find a batch-code-shaped token with NO keyword requirement -- for
    windowed search on lines near a confirmed batch-keyword line, when the
    code itself ended up on a different (unmerged) line."""
    match = BATCH_VALUE_PATTERN.search(text)
    return match.group(0) if match else None


def find_batch_number(text: str) -> Optional[str]:
    match = BATCH_PATTERN.search(text)
    return match.group(1) if match else None
