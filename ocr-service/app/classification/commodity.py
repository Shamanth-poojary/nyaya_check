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
    "Biscuits": ["biscuit", "biscuits", "cookie", "cookies"],
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
    # Snacks: "bhujia" and "savoury" added for Haldiram's-style labels where
    # the decorative 'INDIAN SNACKS' badge text may be absent or OCR-merged.
    "Snacks": ["namkeen", "chips", "snack", "snacks", "bhujia", "savoury", "savory", "sev", "mixture", "potato chips"],
    # Dairy: covers UHT milk cartons (Nandini), flavoured milk, curd, ghee, butter.
    # 'cream' deliberately excluded -- it overlaps with the Cosmetic category
    # and causes false positives on personal-care labels (shampoo, lotion).
    "Dairy": ["milk", "toned milk", "skimmed milk", "full cream milk",
               "pasteurized milk", "uht milk", "curd", "yogurt", "ghee",
               "paneer", "dairy", "butter"],
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


# Prominent Indian & Global FMCG brands encountered in statutory packaged commodity enforcement
KNOWN_BRAND_PATTERNS = [
    # (regex pattern, canonical brand display, optional category hint)
    (r"\bparle[- ]?g\b", "Parle-G", "Biscuits"),
    (r"\bparle\b", "Parle", "Biscuits"),
    (r"\btetley\b", "Tetley", "Tea"),
    (r"\bamul\b", "Amul", "Dairy"),
    (r"\btata\s*tea\b", "Tata Tea", "Tea"),
    (r"\btata\s*salt\b", "Tata Salt", "Salt"),
    (r"\btata\b", "Tata", None),
    (r"\bmarie\s*gold\b", "Marie Gold", "Biscuits"),
    (r"\bmarie\b", "Marie", "Biscuits"),
    (r"\bbritannia\b", "Britannia", "Biscuits"),
    (r"\bhaldiram(?:'s)?\b", "Haldiram's", "Snacks"),
    (r"\blay'?s\b", "Lay's", "Snacks"),
    (r"\bkurkure\b", "Kurkure", "Snacks"),
    (r"\bbingo\b", "Bingo", "Snacks"),
    (r"\bsunfeast\b", "Sunfeast", "Biscuits"),
    (r"\baashirvaad\b", "Aashirvaad", "Flour"),
    (r"\bpatanjali\b", "Patanjali", None),
    (r"\bdabur\b", "Dabur", None),
    (r"\bsaffola\b", "Saffola", "Edible Oil"),
    (r"\bfortune\b", "Fortune", "Edible Oil"),
    (r"\bcadbury\b", "Cadbury", "Snacks"),
    (r"\boreo\b", "Oreo", "Biscuits"),
    (r"\bgood\s*day\b", "Good Day", "Biscuits"),
    (r"\bmonaco\b", "Monaco", "Biscuits"),
    (r"\bfrooti\b", "Frooti", "Beverage"),
    (r"\bmaaza\b", "Maaza", "Beverage"),
    (r"\bthums\s*up\b", "Thums Up", "Beverage"),
    (r"\bsprite\b", "Sprite", "Beverage"),
    (r"\bcoca[- ]?cola\b", "Coca-Cola", "Beverage"),
    (r"\bpepsi\b", "Pepsi", "Beverage"),
    (r"\blimca\b", "Limca", "Beverage"),
    (r"\bbisleri\b", "Bisleri", "Packaged Drinking Water"),
    (r"\bnandini\b", "Nandini", "Dairy"),
    (r"\bmother\s*dairy\b", "Mother Dairy", "Dairy"),
    (r"\bnestle\b", "Nestle", None),
    (r"\bmaggi\b", "Maggi", "Snacks"),
    (r"\bclassic\s*salted\b", "Classic Salted", "Snacks"),
    (r"\bswadeshi\b", "Swadeshi", "Beverage"),
    (r"\bhana\b", "hana", "Beverage"),
]

EXCLUSION_KEYWORDS = [
    "ingredient", "manufactured", "packed by", "marketed by", "consumer care",
    "customer care", "net weight", "net wt", "net qty", "net quantity", "net contents",
    "mrp", "pkd", "mfd", "hfd", "exp", "batch", "use by", "best before", "fssai", "lic. no",
    "lic no", "regd", "pvt ltd", "ltd", "nutrition", "energy", "protein", "carbohydrate",
    "sugar", "fat", "sodium", "approx", "values per", "bengaluru", "mumbai", "delhi",
    "kolkata", "india", "road", "crossing", "phone", "email", "website", "keep your",
    "flavour", "colour", "raising agent", "emulsifier", "preservative", "contains",
    "traces of", "prepared with", "typical values", "airtight", "store in", "good food",
    "good mood", "utterly butterly", "serving", "per 100", "gaseous", "warning",
    "direction", "feedback", "manager", "officer", "sector", "phase", "enclave", "plot no",
    "midc", "ranjangaon", "shirur", "dlf", "qutab", "pioneer square"
]

COMMODITY_DESCRIPTORS = [
    "green tea", "black tea", "tea", "butter", "biscuits", "biscuit", "cookies", "cookie",
    "chips", "potato chips", "namkeen", "bhujia", "atta", "salt", "sugar", "soft drink", "soda", "juice",
    "oil", "pasteurised", "pasteurized", "milk", "toned milk", "gold", "premium",
    "original gluco", "gluco", "salted"
]


def clean_brand_text(text: str) -> str:
    cleaned = re.sub(r"[®™©\"]", "", text)
    cleaned = re.sub(r"[\*#_]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_boilerplate(text: str) -> bool:
    low = text.lower().strip()
    if len(low) < 2:
        return True
    if re.match(r"^[\d\s\.\,\:\;\-\#\/\(\)\%\*\"]+$", low):
        return True
    # Statutory & technical metadata prefixes (e.g. B.NO:, HFD:, EXP:, MRP:, USP:)
    if re.match(r"^(?:b\.?no|batch|lot|pkg|mrp|usp|hfd|mfd|pkd|exp|use by|best before|net wt|net qty|net quantity|fssai|lic\.?)\b", low):
        return True
    # Date expressions (e.g. 26/03/2026)
    if re.search(r"\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4}", low):
        return True
    # Price & currency expressions (e.g. :RS 40, Rs. 20)
    if re.search(r"(?:rs|inr|₹)\s*[:\.]?\s*\d+", low):
        return True
    # Mixed alphanumeric code with colon (like B.NO:MNGMARDYI14)
    if ":" in low and any(c.isdigit() for c in low):
        return True
    for kw in EXCLUSION_KEYWORDS:
        if kw in low:
            return True
    return False


def extract_brand_and_commodity(lines: list) -> Tuple[Optional[str], Optional[str], float]:
    """Extract brand name, commodity title, and category hint by analyzing
    OCR typography, bounding box area dominance, and brand pattern matching.

    Returns:
        (brand_name, category_hint, confidence)
    """
    clean_candidates = []
    for l in lines:
        t = getattr(l, "text", "").strip()
        if not t or is_boilerplate(t):
            continue

        bbox = getattr(l, "bbox", None)
        if bbox is not None:
            # Handle both BoundingBox schema and [xmin, ymin, xmax, ymax]
            if hasattr(bbox, "ymin"):
                area = (bbox.ymax - bbox.ymin) * (bbox.xmax - bbox.xmin)
                h = bbox.ymax - bbox.ymin
            elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                area = (bbox[3] - bbox[1]) * (bbox[2] - bbox[0])
                h = bbox[3] - bbox[1]
            else:
                area, h = 100, 10
        else:
            area, h = 100, 10

        conf = getattr(l, "confidence", 0.9)
        clean_candidates.append({
            "line": l,
            "text": t,
            "area": area,
            "height": h,
            "confidence": conf
        })

    if not clean_candidates:
        return None, None, 0.0

    # Sort candidates by visual prominence: area and line height
    clean_candidates.sort(key=lambda x: (x["area"], x["height"]), reverse=True)

    brand_hit = None
    brand_candidate = None
    category_hint = None

    # 1. Match against known brand dictionary patterns
    for c in clean_candidates:
        low = c["text"].lower()
        for pattern, display, cat in KNOWN_BRAND_PATTERNS:
            if re.search(pattern, low):
                brand_hit = display
                brand_candidate = c
                category_hint = cat
                break
        if brand_hit:
            break

    # Look for complementary product descriptor (e.g. "GREEN TEA", "BUTTER", "Original Gluco Biscuits")
    descriptor_hit = None
    for c in clean_candidates:
        if brand_candidate and c == brand_candidate:
            continue
        low = c["text"].lower()
        for desc in COMMODITY_DESCRIPTORS:
            if desc in low:
                descriptor_hit = c["text"]
                break
        if descriptor_hit:
            break

    final_name = None
    final_conf = 0.85

    if brand_hit:
        final_conf = max(brand_candidate["confidence"], 0.85)
        if descriptor_hit:
            desc_clean = clean_brand_text(descriptor_hit)
            if desc_clean.lower() not in brand_hit.lower():
                desc_title = " ".join(w.capitalize() for w in desc_clean.split())
                final_name = f"{brand_hit} {desc_title}"
            else:
                final_name = brand_hit
        else:
            final_name = brand_hit
    else:
        # Fallback: visually most prominent title on PDP (requires minimum height/area to avoid small body text)
        top = clean_candidates[0]
        # Must have reasonable area / height and alphabetic content
        letters = sum(1 for c in top["text"] if c.isalpha())
        if letters >= 3 and (top["area"] >= 2000 or top["height"] >= 20):
            final_name = clean_brand_text(top["text"])
            final_conf = max(top["confidence"], 0.80)
            if len(clean_candidates) > 1:
                second = clean_candidates[1]
                if second["area"] > 0.4 * top["area"]:
                    low_sec = second["text"].lower()
                    if any(d in low_sec for d in COMMODITY_DESCRIPTORS):
                        desc_title = " ".join(w.capitalize() for w in clean_brand_text(second["text"]).split())
                        final_name = f"{final_name} {desc_title}"
        else:
            return None, None, 0.0

    return final_name, category_hint, final_conf


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
