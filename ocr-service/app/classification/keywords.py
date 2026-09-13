"""
Keyword matching: identifies context (which role, which date type, which
qualifier) so regex hits can be assigned meaning, and finds phrases that
carry legal significance even without an associated number.

Includes tolerance for known OCR misreads seen in real test photos (e.g.
'HFD' for 'MFD' -- M/H confusion in dot-matrix print) rather than assuming
clean input.
"""

import re
from typing import List, Optional

# --- Fuzzy matching for short abbreviations ------------------------------------
#
# Short labels (MRP, EXP, MFD -- 3-4 chars) are the most fragile to OCR noise:
# a single misread character changes the whole word ('MRP' -> 'MRE', 'EXP' ->
# 'EXF'). Exact substring matching breaks on these; edit-distance tolerance
# doesn't. Longer phrases ('Manufactured by', 'Customer Care') are more
# robust already (more characters to get right), so they stay on plain
# substring matching -- fuzzy-matching long phrases risks false positives.

def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


def _fuzzy_word_in(text: str, keyword: str, max_distance: int = 1) -> bool:
    """True if any word in `text` is within `max_distance` edits of `keyword`."""
    for word in re.findall(r"[A-Za-z]+", text):
        if abs(len(word) - len(keyword)) <= max_distance and _levenshtein(word.lower(), keyword.lower()) <= max_distance:
            return True
    return False


FUZZY_ABBREVIATIONS = {
    "mfd": "manufacturing", "hfd": "manufacturing", "mfg": "manufacturing",
    "exp": "expiry", "exf": "expiry",
    "pkd": "packing",
    "mrp": "MRP",
}

# --- Party role headers ------------------------------------------------------

MANUFACTURER_ONLY_KEYWORDS = ["manufactured by", "manufactured & marketed by", "mfg by", "mfd by"]
PACKER_ONLY_KEYWORDS = ["packed by", "packer"]
IMPORTER_KEYWORDS = ["imported by", "importer"]
MARKETER_KEYWORDS = ["marketed by"]

# Combined phrasing -- extremely common on real labels ("Manufactured &
# Packed by X") where ONE entity fills multiple roles. Checked before the
# single-role keywords below, since e.g. "packed by" is a substring of
# "manufactured & packed by" and would otherwise steal the match and
# silently drop the manufacturer role entirely.
COMBINED_ROLE_KEYWORDS = [
    (["manufactured & packed by", "manufactured and packed by"], ["manufacturer", "packer"]),
    (["manufactured & marketed by", "manufactured and marketed by"], ["manufacturer"]),
]

CONSUMER_CARE_KEYWORDS = ["customer care", "consumer care", "consumer complaint"]


def match_role_keyword(text: str) -> Optional[List[str]]:
    """Return the list of applicable roles ('manufacturer' | 'packer' |
    'importer' | 'marketer') if this line's text contains a role header,
    else None. A list, not a single role, because real labels commonly
    name ONE entity for multiple roles at once ("Manufactured & Packed by
    X") -- collapsing that to a single role silently drops information."""
    lowered = text.lower()

    for phrases, roles in COMBINED_ROLE_KEYWORDS:
        if any(p in lowered for p in phrases):
            return roles

    if any(k in lowered for k in MANUFACTURER_ONLY_KEYWORDS):
        return ["manufacturer"]
    if any(k in lowered for k in PACKER_ONLY_KEYWORDS):
        return ["packer"]
    if any(k in lowered for k in IMPORTER_KEYWORDS):
        return ["importer"]
    if any(k in lowered for k in MARKETER_KEYWORDS):
        return ["marketer"]
    return None


def is_consumer_care_line(text: str) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in CONSUMER_CARE_KEYWORDS)


# --- Date-type keywords (with OCR-misread tolerance) --------------------------

# 'HFD' included deliberately: observed OCR misread of 'MFD' in real test
# photos (M/H confusion in dot-matrix print). Don't assume clean input.
# 'HFD' included deliberately: observed OCR misread of 'MFD' in real test
# photos (M/H confusion in dot-matrix print). Don't assume clean input.
MANUFACTURING_DATE_KEYWORDS = ["manufactured", "date of manufacture"]
EXPIRY_DATE_KEYWORDS = ["expiry", "best before", "use by"]
PACKING_DATE_KEYWORDS = ["packed on", "packing date", "date of packaging"]


def match_date_type_keyword(text):
    """Return 'manufacturing' | 'expiry' | 'packing' if this line's text
    contains a date-type keyword, else None. Short abbreviations (MFD, HFD,
    EXP, EXF, PKD) use fuzzy matching since a single misread character
    changes the whole word; longer phrases use exact substring matching."""
    lowered = text.lower()
    if any(re.search(rf"\b{re.escape(k)}\b", lowered) for k in EXPIRY_DATE_KEYWORDS):
        return "expiry"
    if any(re.search(rf"\b{re.escape(k)}\b", lowered) for k in PACKING_DATE_KEYWORDS):
        return "packing"
    if any(re.search(rf"\b{re.escape(k)}\b", lowered) for k in MANUFACTURING_DATE_KEYWORDS):
        return "manufacturing"
    for abbr, date_type in FUZZY_ABBREVIATIONS.items():
        if date_type in ("manufacturing", "expiry", "packing") and _fuzzy_word_in(text, abbr):
            return date_type
    return None


# --- Net quantity keywords -----------------------------------------------------

NET_QUANTITY_KEYWORDS = [
    "net qty", "net quantity", "net wt", "net weight", "net vol", "net volume",
    "net contents",  # "Net Contents:" is a common real-label phrasing
]


def is_net_quantity_line(text: str) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in NET_QUANTITY_KEYWORDS)


# --- Quantity qualifiers (legally significant phrases) -------------------------

QUANTITY_QUALIFIERS = {
    "when packed": "WHEN_PACKED",
    "minimum": "MINIMUM",
    "not less than": "NOT_LESS_THAN",
    "average": "AVERAGE",
}

MISLEADING_TERMS = ["approximately", "about", "dozen"]


def find_quantity_qualifiers(text: str) -> List[dict]:
    lowered = text.lower()
    hits = []
    for phrase, qualifier_type in QUANTITY_QUALIFIERS.items():
        if phrase in lowered:
            hits.append({"text": phrase, "qualifierType": qualifier_type})
    return hits


def find_misleading_terms(text: str) -> List[str]:
    lowered = text.lower()
    return [term for term in MISLEADING_TERMS if term in lowered]
