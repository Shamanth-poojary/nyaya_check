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

# --- Party role headers ------------------------------------------------------

MANUFACTURER_KEYWORDS = ["manufactured by", "manufactured & marketed by", "mfg by", "mfd by"]
PACKER_KEYWORDS = ["packed by", "packer"]
IMPORTER_KEYWORDS = ["imported by", "importer"]
MARKETER_KEYWORDS = ["marketed by"]

CONSUMER_CARE_KEYWORDS = ["customer care", "consumer care", "consumer complaint"]


def match_role_keyword(text: str) -> Optional[str]:
    """Return 'manufacturer' | 'packer' | 'importer' | 'marketer' if this
    line's text contains a role header, else None."""
    lowered = text.lower()
    if any(k in lowered for k in MANUFACTURER_KEYWORDS):
        return "manufacturer"
    if any(k in lowered for k in PACKER_KEYWORDS):
        return "packer"
    if any(k in lowered for k in IMPORTER_KEYWORDS):
        return "importer"
    if any(k in lowered for k in MARKETER_KEYWORDS):
        return "marketer"
    return None


def is_consumer_care_line(text: str) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in CONSUMER_CARE_KEYWORDS)


# --- Date-type keywords (with OCR-misread tolerance) --------------------------

# 'HFD' included deliberately: observed OCR misread of 'MFD' in real test
# photos (M/H confusion in dot-matrix print). Don't assume clean input.
MANUFACTURING_DATE_KEYWORDS = ["mfd", "hfd", "mfg", "manufactured", "date of manufacture", "mfd."]
EXPIRY_DATE_KEYWORDS = ["exp", "expiry", "best before", "use by", "exp."]
PACKING_DATE_KEYWORDS = ["pkd", "packed on", "packing date"]


def match_date_type_keyword(text: str) -> Optional[str]:
    """Return 'manufacturing' | 'expiry' | 'packing' if this line's text
    contains a date-type keyword, else None."""
    lowered = text.lower()
    if any(re.search(rf"\b{re.escape(k)}\b", lowered) for k in EXPIRY_DATE_KEYWORDS):
        return "expiry"
    if any(re.search(rf"\b{re.escape(k)}\b", lowered) for k in PACKING_DATE_KEYWORDS):
        return "packing"
    if any(re.search(rf"\b{re.escape(k)}\b", lowered) for k in MANUFACTURING_DATE_KEYWORDS):
        return "manufacturing"
    return None


# --- Net quantity keywords -----------------------------------------------------

NET_QUANTITY_KEYWORDS = ["net qty", "net quantity", "net wt", "net weight", "net vol", "net volume"]


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
