"""
app/rules/schedules.py — Schedule 2/3 commodity lookup helpers.

Loads `app/rules/data/standard_quantities.yaml` once at module import time
and exposes three pure query functions used by the rule modules.

NO imports from app.ocr, app.preprocessing, or app.classification.

TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15
"""

from __future__ import annotations

import pathlib
from typing import List, Optional, Set, Tuple

import yaml

# ---------------------------------------------------------------------------
# Load YAML once at import
# ---------------------------------------------------------------------------

_DATA_FILE = pathlib.Path(__file__).parent / "data" / "standard_quantities.yaml"

with _DATA_FILE.open(encoding="utf-8") as _fh:
    _SCHEDULE_DATA: dict = yaml.safe_load(_fh)


# ---------------------------------------------------------------------------
# SI unit sets, keyed by quantity_type name
# ---------------------------------------------------------------------------
# These are used by rules_11_17_quantity.py to validate that
# netQuantity.unit is appropriate for netQuantity.quantityType.
# TODO: verify against current Legal Metrology Rules text, last checked: 2026-09-15

SI_UNITS_BY_TYPE: dict[str, Set[str]] = {
    "weight": {"g", "kg", "mg"},
    "mass": {"g", "kg", "mg"},
    "volume": {"ml", "l", "cl"},
    "length": {"m", "cm", "mm"},
    "count": {"No", "N", "no", "n", "nos", "Nos"},
    "area": {"m2", "cm2", "sqm", "sqcm"},
}

# Normalised aliases → canonical quantity_type
_UNIT_TO_TYPE: dict[str, str] = {
    "g": "weight", "kg": "weight", "mg": "weight",
    "ml": "volume", "l": "volume", "cl": "volume",
    "m": "length", "cm": "length", "mm": "length",
    "No": "count", "N": "count", "no": "count", "n": "count",
    "nos": "count", "Nos": "count",
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def dimensions_required(category: Optional[str]) -> bool:
    """Return True if the commodity category requires dimensions on the label
    under Rule 6 read with the Fourth Schedule.

    Returns False for any category not in the data file (fail-open: don't
    flag a missing-dimensions violation for unknown categories, since we have
    no authoritative data for them).
    """
    if not category:
        return False
    entry = _SCHEDULE_DATA.get(category)
    if entry is None:
        return False
    return bool(entry.get("dimensions_required", False))


def permitted_qualifier_types(category: Optional[str]) -> Set[str]:
    """Return the set of qualifier types (WHEN_PACKED, MINIMUM, etc.) that
    are permitted for the given commodity category.

    Returns an empty set for unknown categories, meaning any qualifier present
    will be flagged — conservative and explicit.
    """
    if not category:
        return set()
    entry = _SCHEDULE_DATA.get(category)
    if entry is None:
        return set()
    return set(entry.get("permitted_qualifier_types", []))


def standard_quantities(category: Optional[str]) -> List[Tuple[float, str]]:
    """Return the list of (value, unit) standard package sizes for the
    category from Schedule 2/3.

    Returns an empty list for unknown categories.
    """
    if not category:
        return []
    entry = _SCHEDULE_DATA.get(category)
    if entry is None:
        return []
    raw = entry.get("standard_quantities", [])
    return [(float(pair[0]), str(pair[1])) for pair in raw if pair]


def is_unit_valid_for_type(unit: Optional[str], quantity_type: Optional[str]) -> bool:
    """Return True if the given SI unit is appropriate for the declared
    quantity type (weight/volume/length/count).

    Returns True (pass-through) when either argument is None or empty,
    because the absence of those fields is checked separately in Rule 6.
    """
    if not unit or not quantity_type:
        return True

    qt_lower = quantity_type.lower()
    allowed_units = SI_UNITS_BY_TYPE.get(qt_lower, set())
    if allowed_units:
        return unit in allowed_units

    # quantity_type not in our map — infer from unit
    inferred = _UNIT_TO_TYPE.get(unit)
    if inferred is None:
        # Unknown unit: can't validate, return True (let it pass — logged via NEEDS_REVIEW elsewhere)
        return True
    return inferred == qt_lower


def category_has_schedule_data(category: Optional[str]) -> bool:
    """Return True if the category has Schedule 2/3 data in the YAML.

    Used to distinguish 'uncovered category — silently skip' from
    'covered category — apply checks'.
    """
    if not category:
        return False
    return category in _SCHEDULE_DATA
