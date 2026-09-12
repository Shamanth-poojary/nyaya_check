"""
Phase 6: commodity/category classification.

Legal Metrology schedules reference commodity-SPECIFIC quantity
requirements and permitted units (Second/Third Schedule), so knowing the
product's category -- not just extracting its brand name -- is needed for
the rules engine to apply the right checks downstream.

This is deliberately a coarse, keyword-based first pass. A real product
taxonomy or NER-based brand/product matching would do better, but keyword
matching against manufacturer names, domains, and descriptive label text
already gets real signal: on the actual "hana" test photos, neither photo
has a dedicated "product type" field anywhere, yet "Swadeshi Food &
BEVERAGES" (manufacturer name) and "hanaDRINKS.in" (website) both leak the
category without either being an explicit declaration -- keyword matching
against the FULL text picks that up; a stricter field-by-field parser
would miss it entirely.

`commodity.name` (the specific product/brand name) is deliberately left
unset here -- reliably extracting "Coca-Cola" vs "Thums Up" vs "hana" from
label text without a product database is a different, harder problem than
category classification, and guessing wrong is worse than leaving it None.
"""

import re
from typing import List, Optional, Tuple

# category -> keywords indicative of that category. Word-boundary matched
# (case-insensitive) so short words like "tea" don't false-positive inside
# unrelated words. Not exhaustive -- extend as new commodity types show up
# in real test photos.
CATEGORY_KEYWORDS = {
    "Tea": ["tea", "chai"],
    "Biscuits": ["biscuit", "cookie"],
    "Rice": ["rice", "basmati"],
    "Salt": ["salt", "namak"],
    "Sugar": ["sugar"],
    "Edible Oil": ["edible oil", "cooking oil", "refined oil", "sunflower oil", "mustard oil"],
    "Spices": ["spice", "masala", "turmeric", "chilli powder", "coriander powder"],
    "Pulses": ["dal", "pulses", "lentil"],
    "Flour": ["atta", "flour", "maida"],
    "Honey": ["honey"],
    "Milk Powder": ["milk powder", "infant formula"],
    "Beverage": ["beverage", "soft drink", "juice", "soda", "healthy drink", "drinks"],
    "Packaged Drinking Water": ["packaged drinking water", "mineral water"],
    "Snacks": ["namkeen", "chips", "snack"],
    "Soap": ["soap", "bathing bar"],
    "Detergent": ["detergent", "washing powder"],
    "Toothpaste": ["toothpaste", "tooth paste"],
    "Cosmetic": ["cream", "lotion", "cosmetic", "moisturizer", "shampoo", "conditioner"],
    "Paint": ["paint", "enamel", "emulsion"],
    "Ready-made Garment": ["garment", "apparel"],
    "Tyre": ["tyre", "tire"],
    "Cable": ["cable", "wire gauge"],
}


SHORT_KEYWORD_LENGTH = 4  # keywords at or below this length need word boundaries
                          # (e.g. "tea" inside "instead"); longer keywords are safe
                          # to substring-match, and NEED to be -- real labels have
                          # plurals ("Beverages") and concatenated text
                          # ("hanadrinks.in") that strict \bword\b matching misses.


def _count_keyword_hits(text: str, keywords: List[str]) -> int:
    hits = 0
    lowered = text.lower()
    for kw in keywords:
        if len(kw) <= SHORT_KEYWORD_LENGTH:
            if re.search(rf"\b{re.escape(kw)}\b", lowered):
                hits += 1
        elif kw.lower() in lowered:
            hits += 1
    return hits


def classify_commodity(all_text: str) -> Optional[Tuple[str, float]]:
    """Return (category, confidence) for the best-matching category across
    the full text of a product's label(s), or None if nothing matched.

    Confidence is heuristic (more keyword hits = more confident) and
    capped at 0.85 -- this method is coarse and should never claim the
    certainty a real product-database lookup would earn.
    """
    best_category = None
    best_hits = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = _count_keyword_hits(all_text, keywords)
        if hits > best_hits:
            best_hits = hits
            best_category = category

    if best_category is None:
        return None

    confidence = min(0.5 + 0.15 * best_hits, 0.85)
    return best_category, confidence
