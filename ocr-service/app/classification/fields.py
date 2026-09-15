"""
Phase 5 field classifier.

Walks rawOCR lines (already sorted top-to-bottom) and populates the named
fields on ExtractionResponse using a hybrid of regex, keyword matching, and
simple vertical-proximity ("what's on the next few lines") spatial
reasoning. rawOCR itself is left untouched -- this only ADDS structure on
top of it, per "Preserve Three Levels of Data" in the project plan.

Deliberately conservative: if something looks ambiguous (e.g. a quantity
number that might be a unit price, not a net quantity), it's left
unclassified and noted in uncertainFields rather than guessed at. A missed
field is safer than a wrongly-filled one -- a downstream rules engine can
flag "not found", but can't un-trust a wrong value it doesn't know is wrong.
"""

from typing import List, Optional

import re
from app.classification import commodity, keywords, regex
from app.schemas.response import (
    BatchNumber,
    DateField,
    Dimension,
    ExtractionResponse,
    MisleadingTerm,
    MRP,
    NetQuantity,
    PartyInfo,
    QuantityQualifier,
    RawOCRLine,
)

# Lines containing these should never be treated as a net-quantity candidate,
# even though they contain a number+unit -- they're a different field that
# happens to share the same shape (e.g. "USP :RS 0.07ML" is unit selling
# PRICE per ml, not the product's net quantity).
NET_QTY_EXCLUSION_KEYWORDS = [
    "usp", "unit selling price", "per unit", "mrp",
    "per 100", "per100", "per serving", "approximate value",  # nutrition-panel refs, not the declared net qty
]

NET_QTY_SEARCH_WINDOW = 3  # lines to check after a "Net Qty"/"Net Contents" keyword line
                           # for its value -- real labels often put label and
                           # value on separate physical lines, not just split
                           # detections (see: "Net Contents:" / "600 ml")


READING_ORDER_ROW_TOLERANCE = 8  # pixels; deliberately tight -- this only needs to
                                   # correct small same-row bbox-height discrepancies
                                   # (e.g. a keyword's letter-height vs its value's
                                   # digit-height, often just a few px), NOT group
                                   # genuinely separate, sequential lines of text
                                   # (which have normal line spacing, typically 15px+)


def _reading_order(lines: List[RawOCRLine]) -> List[RawOCRLine]:
    """Sort lines into genuine reading order: row by row (grouped by
    vertical CENTER proximity, not raw ymin), left-to-right within each
    row. A plain sort-by-ymin can misorder two same-row fragments when
    their bounding boxes have slightly different heights -- e.g. a
    keyword's letters vs. its value's digits -- which silently broke
    windowed searches that only look FORWARD for a value (the value
    would sort BEFORE its own keyword). Same underlying fix as the
    line-merging row-clustering in app/ocr/normalize.py, applied here to
    classification's reading order instead of merging.
    """
    def center_y(l: RawOCRLine) -> float:
        return (l.bbox.ymin + l.bbox.ymax) / 2

    by_center = sorted(lines, key=center_y)
    rows: List[List[RawOCRLine]] = []
    row_centers: List[float] = []

    for line in by_center:
        c = center_y(line)
        if rows and abs(c - row_centers[-1]) <= READING_ORDER_ROW_TOLERANCE:
            rows[-1].append(line)
            row_centers[-1] = sum(center_y(l) for l in rows[-1]) / len(rows[-1])
        else:
            rows.append([line])
            row_centers.append(c)

    ordered: List[RawOCRLine] = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda l: l.bbox.xmin))
    return ordered


def classify_fields(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    """Mutates `response` in place based on `lines` (response.rawOCR)."""
    ordered = _reading_order(lines)

    consumed_indices: set = set()

    _classify_mrp(response, ordered)
    _classify_net_quantity(response, ordered)
    _classify_dates(response, ordered)
    _classify_batch_number(response, ordered)
    _classify_dimensions(response, ordered)
    _classify_party_blocks(response, ordered, consumed_indices)
    _classify_consumer_care(response, ordered)
    _classify_qualifiers_and_misleading_terms(response, ordered)
    _classify_commodity(response, ordered)



# Section-boundary keywords: once we hit an ingredients list, we stop
# treating text as category signal until we see one of these -- otherwise
# a beverage listing "Salt" as an ingredient gets misclassified as the
# category "Salt". Deliberately plain substring checks (not full regex
# parsing) since we only need a "new section started" signal, not a
# successful field extraction.
SECTION_BOUNDARY_KEYWORDS = [
    "mrp", "net qty", "net quantity", "net wt", "net weight", "net contents",
    "mfg", "mfd", "hfd", "exp", "batch", "b.no",
    "manufactured", "packed by", "imported by", "customer care", "consumer care",
]


def _classify_commodity(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    """Phase 6: coarse category classification from the FULL label text --
    not any single line -- since category signal often comes from the
    manufacturer's name or website domain rather than an explicit
    'product type' declaration (see commodity.py docstring).

    Ingredient lists are explicitly excluded: a product's ingredients
    (e.g. "Sugar, Salt, Acidity Regulator") are not its category, but
    share vocabulary with real category keywords (Salt, Sugar, Honey,
    Rice...), so naive whole-document matching misclassifies real products.
    """
    ingredients_idx = next(
        (i for i, l in enumerate(lines) if re.search(r"\bingredients\b", l.text, re.IGNORECASE)), None
    )

    if ingredients_idx is None:
        kept_lines = lines
    else:
        end_idx = len(lines)
        for i in range(ingredients_idx + 1, len(lines)):
            lowered = lines[i].text.lower()
            if any(kw in lowered for kw in SECTION_BOUNDARY_KEYWORDS):
                end_idx = i
                break
        kept_lines = lines[:ingredients_idx] + lines[end_idx:]

    all_text = " ".join(line.text for line in kept_lines)
    hit = commodity.classify_commodity(all_text)
    if hit:
        category, confidence = hit
        response.commodity.category = category
        response.commodity.found = True
        response.commodity.confidence = confidence


MRP_SEARCH_WINDOW = 3  # lines to check after an 'MRP' keyword line for its
                       # amount -- real labels sometimes leave label and
                       # value on separate lines that don't quite merge
                       # (narrowly missed geometry, wrapped text, etc.)


SEE_PRINTED_ELSEWHERE_PATTERN = re.compile(
    r"\bsee\s+(?:neck|cap|lid|crown|bottom|pouch|pkg|pack|below|reverse|side)\b",
    re.IGNORECASE,
)


def _classify_mrp(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    # A single photo can have multiple MRP-like lines (e.g. front-of-pack
    # promotional callout vs back-of-pack compliance block). We score ALL
    # matches and keep the highest-confidence one, rather than returning on
    # the first match we encounter.
    candidates = []
    for i, line in enumerate(lines):
        result = regex.find_mrp(line.text)
        if result is not None:
            value, tax_included = result
            if tax_included is None and i + 1 < len(lines):
                next_line = lines[i + 1]
                if regex.TAX_INCLUDED_PATTERN.search(next_line.text):
                    tax_included = True
            candidates.append((value, tax_included, line))
            continue

        # Keyword present but no valid amount on THIS line (either no
        # number at all, or the only number found was rejected as a
        # quantity) -- check nearby lines before giving up. Collect ALL
        # candidates in the window rather than stopping at the first --
        # a low-confidence OCR artifact (e.g. a garbled decorative
        # fragment) can appear before the real, high-confidence value.
        if regex.is_mrp_line(line.text):
            # If this line or the immediate next line explicitly defers to another location
            # (e.g. "(Incl of all taxes) See Neck", "MRP: See Cap"), then the price is
            # intentionally printed on another part of the container. Do not grab random numbers
            # from surrounding nutrition/legal text on this image.
            next_text = lines[i + 1].text if i + 1 < len(lines) else ""
            if SEE_PRINTED_ELSEWHERE_PATTERN.search(line.text) or SEE_PRINTED_ELSEWHERE_PATTERN.search(next_text):
                continue

            window_candidates = []
            # Forward window: most common case (value below keyword).
            for j in range(i + 1, min(i + 1 + MRP_SEARCH_WINDOW, len(lines))):
                candidate_line = lines[j]
                bare_value = regex.find_bare_amount(candidate_line.text)
                if bare_value is not None:
                    window_candidates.append((bare_value, candidate_line))

            # Backward window: fallback for same-physical-row layouts where
            # a glyph-height difference causes the value's bbox to sort
            # fractionally above the keyword in reading order -- the
            # forward-only search silently misses it in that case.
            # Only searched if the forward window found nothing, preserving
            # forward-first priority.
            if not window_candidates:
                for j in range(max(0, i - MRP_SEARCH_WINDOW), i):
                    candidate_line = lines[j]
                    if not (_is_same_row(line, candidate_line) or _is_same_column(line, candidate_line)):
                        continue
                    bare_value = regex.find_bare_amount(candidate_line.text)
                    if bare_value is not None:
                        window_candidates.append((bare_value, candidate_line))

            if window_candidates:
                bare_value, best_line = max(window_candidates, key=lambda c: c[1].confidence)
                tax_included = bool(regex.TAX_INCLUDED_PATTERN.search(line.text + " " + best_line.text)) or None
                candidates.append((bare_value, tax_included, best_line))

    if not candidates:
        return

    if len(candidates) > 1:
        response.uncertainFields.append(
            f"Multiple MRP-like values found ({len(candidates)}); used the highest-confidence one."
        )

    value, tax_included, line = max(candidates, key=lambda c: c[2].confidence)
    response.mrp = MRP(
        value=value,
        taxIncluded=tax_included,
        raw=line.text,
        bbox=line.bbox,
        found=True,
        confidence=line.confidence,
    )


def _classify_net_quantity(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    # Prefer a "Net Qty"/"Net Contents" keyword line, then search a small
    # window of NEARBY lines (not just the same line) for the value --
    # real labels sometimes put the label and value on separate physical
    # lines (e.g. "Net Contents:" then "600 ml" below it).
    #
    # Also searches BACKWARD from the keyword line (up to NET_QTY_SEARCH_WINDOW
    # lines before it) because on rotated / perspective-distorted photos the
    # OCR sorts text by ymin in the skewed coordinate system -- so "250 g" may
    # sort earlier than "NET QUANTITY:" even though they are visually adjacent.
    for i, line in enumerate(lines):
        if not keywords.is_net_quantity_line(line.text):
            continue

        hit = regex.find_net_quantity(line.text)
        if hit:
            response.netQuantity = NetQuantity(bbox=line.bbox, found=True, confidence=line.confidence, **hit)
            return

        # Forward window: value is below the keyword line
        for j in range(i + 1, min(i + 1 + NET_QTY_SEARCH_WINDOW, len(lines))):
            candidate = lines[j]
            hit = regex.find_net_quantity(candidate.text)
            if hit:
                response.netQuantity = NetQuantity(
                    bbox=candidate.bbox, found=True, confidence=candidate.confidence, **hit
                )
                return

        # Backward window: value sorted before the keyword (rotated label case)
        for j in range(max(0, i - NET_QTY_SEARCH_WINDOW), i):
            candidate = lines[j]
            hit = regex.find_net_quantity(candidate.text)
            if hit:
                # Extra guard: exclude lines that contain excluded keywords to
                # avoid misclassifying nutritional-panel values that also precede
                # the NQ keyword in a scrambled reading order.
                lowered = candidate.text.lower()
                if any(k in lowered for k in NET_QTY_EXCLUSION_KEYWORDS):
                    continue
                response.netQuantity = NetQuantity(
                    bbox=candidate.bbox, found=True, confidence=candidate.confidence, **hit
                )
                return

    # Fall back to a bare quantity+unit match, but never on excluded lines
    # (unit price, MRP, nutrition-panel "per 100ml" references, etc. share
    # the same "number + unit" shape). Collect ALL candidates rather than
    # stopping at the first hit -- a spurious nutrition-panel match earlier
    # in reading order must not shadow the real value further down.
    candidates = []
    for line in lines:
        lowered = line.text.lower()
        if any(k in lowered for k in NET_QTY_EXCLUSION_KEYWORDS):
            continue
        hit = regex.find_net_quantity(line.text)
        if hit:
            candidates.append((hit, line))

    if candidates:
        hit, line = max(candidates, key=lambda c: c[1].confidence)
        response.uncertainFields.append(
            f"Quantity '{hit['rawValue']}' found without a 'Net Qty' keyword nearby; "
            "not confident this is the declared net quantity -- left unclassified."
        )


def _classify_dates(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    for i, line in enumerate(lines):
        date_hit = regex.find_date(line.text)
        if not date_hit:
            continue
        date_type = keywords.match_date_type_keyword(line.text)
        if date_type is None and i > 0:
            # Common layout: "Use By" (or similar) on its own line, with
            # the date itself on the very next line -- without this,
            # dates default to "manufacturing" even when a keyword is
            # sitting right next to them, just not on the SAME line.
            date_type = keywords.match_date_type_keyword(lines[i - 1].text)
        date_type = date_type or "manufacturing"

        field = DateField(
            raw=line.text,
            dateType=date_type,
            day=date_hit["day"],
            month=date_hit["month"],
            year=date_hit["year"],
            bbox=line.bbox,
            found=True,
            confidence=line.confidence,
        )

        if date_type == "expiry" and not response.expiryDate.found:
            response.expiryDate = field
        elif date_type == "packing" and not response.packingDate.found:
            response.packingDate = field
        elif date_type not in ("expiry", "packing") and not response.manufacturingDate.found:
            response.manufacturingDate = field


BATCH_SEARCH_WINDOW = 3  # lines to check after (or before) a 'Batch No' keyword line


def _is_same_row(a: RawOCRLine, b: RawOCRLine) -> bool:
    """True if lines are on the same visual row (inline horizontally)."""
    a_center = (a.bbox.ymin + a.bbox.ymax) / 2
    b_center = (b.bbox.ymin + b.bbox.ymax) / 2
    return abs(a_center - b_center) <= READING_ORDER_ROW_TOLERANCE


def _classify_batch_number(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    for i, line in enumerate(lines):
        batch = regex.find_batch_number(line.text)
        if batch:
            response.batchNumber = BatchNumber(
                value=batch, raw=line.text, bbox=line.bbox, found=True, confidence=line.confidence,
            )
            return

        if regex.is_batch_line(line.text):
            candidates = []
            # Forward window: most common case (value on the line(s) after
            # the keyword, or adjacent on the same visual row).
            for j in range(i + 1, min(i + 1 + BATCH_SEARCH_WINDOW, len(lines))):
                candidate_line = lines[j]
                if not (_is_same_column(line, candidate_line) or _is_same_row(line, candidate_line)):
                    continue
                bare_batch = regex.find_bare_batch_value(candidate_line.text)
                if bare_batch:
                    candidates.append((bare_batch, candidate_line))

            # Backward window: fallback for same-physical-row layouts where
            # a glyph-height difference causes the value's bbox to sort
            # fractionally ABOVE the keyword in reading order (e.g. 'B0724'
            # bounding box 2 px higher than 'Batch No.' due to digit vs
            # letter height).
            for j in range(max(0, i - BATCH_SEARCH_WINDOW), i):
                candidate_line = lines[j]
                if not (_is_same_column(line, candidate_line) or _is_same_row(line, candidate_line)):
                    continue
                bare_batch = regex.find_bare_batch_value(candidate_line.text)
                if bare_batch:
                    candidates.append((bare_batch, candidate_line))

            if candidates:
                best_val, best_line = max(candidates, key=lambda c: c[1].confidence)
                response.batchNumber = BatchNumber(
                    value=best_val,
                    raw=best_line.text,
                    bbox=best_line.bbox,
                    found=True,
                    confidence=best_line.confidence,
                )
                return


DIMENSION_SEARCH_WINDOW = 3


def _classify_dimensions(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    handled_indices = set()
    for i, line in enumerate(lines):
        if i in handled_indices:
            continue
        dims = regex.find_dimensions(line.text)
        if dims:
            for d in dims:
                response.dimensions.append(
                    Dimension(
                        label=d.get("label"),
                        value=d.get("value"),
                        unit=d.get("unit"),
                        bbox=line.bbox,
                    )
                )
            handled_indices.add(i)
            continue

        # Keyword on this line, value on the next line (e.g. "Size:" \n "40 cm x 60 cm")
        if regex.is_dimension_line(line.text):
            for j in range(i + 1, min(i + 1 + DIMENSION_SEARCH_WINDOW, len(lines))):
                if j in handled_indices:
                    continue
                candidate = lines[j]
                dims = regex.find_dimensions(candidate.text)
                if dims:
                    for d in dims:
                        response.dimensions.append(
                            Dimension(
                                label=d.get("label"),
                                value=d.get("value"),
                                unit=d.get("unit"),
                                bbox=candidate.bbox,
                            )
                        )
                    handled_indices.add(j)
                    break


ROLE_BLOCK_MAX_LINES = 10  # generous window since column-filtering below can
                            # skip several cross-column lines before finding
                            # the next genuine same-column address line


def _is_same_column(a: RawOCRLine, b: RawOCRLine) -> bool:
    """True if lines are stacked in the same column.

    A marginal overlap (e.g. wide text blocks in adjacent columns that
    barely touch) is rejected. At least one line's horizontal center must
    fall within the other line's bounding box to count as the same column.
    """
    a_center = (a.bbox.xmin + a.bbox.xmax) / 2
    b_center = (b.bbox.xmin + b.bbox.xmax) / 2

    a_contains_b = a.bbox.xmin <= b_center <= a.bbox.xmax
    b_contains_a = b.bbox.xmin <= a_center <= b.bbox.xmax

    return a_contains_b or b_contains_a


# Address start indicators: patterns that unambiguously mark where genuine
# postal address content begins. Used by _clean_address_line to strip any
# non-address prefix that OCR has merged onto the same line (e.g. an
# ingredient-list fragment from the adjacent column on the same label row).
#
# Each alternative requires a keyword + digit or a known industrial-estate
# acronym to minimise false positives on ingredient/description words.
_ADDRESS_START_PATTERN = re.compile(
    r"(?:"
    # Keyword + optional 'No.'/'#' + digit: 'Plot No. 7', 'Sector 63', 'Unit 4'
    r"(?:plot|survey|sy\.?|gat|khasra|door|flat|house|unit|phase|block|sector|ward)"
    r"\s*(?:no\.?|#)?\s*\d"
    r"|"
    # Common Indian industrial-estate acronyms that anchor an address:
    # MIDC (Maharashtra), GIDC (Gujarat), SIDC/SIDCO (various states),
    # KIADB (Karnataka), APIIC (Andhra Pradesh)
    r"\b(?:MIDC|GIDC|SIDC|SIDCO|EPIP|KIADB|APIIC|IDA)\b"
    r")",
    re.IGNORECASE,
)


def _clean_address_line(text: str) -> str:
    """Strip any non-address prefix from a merged OCR line.

    When Google Vision (or any OCR engine) encounters two side-by-side columns
    at the same vertical position -- e.g. an ingredient list on the left and
    'Plot No. 145, Sector 63' on the right -- it sometimes emits a SINGLE text
    block whose content reads left-column-text + right-column-text.  That merged
    line ends up in the address field looking like:

        'Gram Flour (Besan), Iodised Salt, Spices & Plot No. 145, Sector 63'

    _clean_address_line finds the first genuine address indicator in the text
    and returns everything from that point onward, discarding the ingredient
    prefix.  If no indicator is found (the line is already clean) the original
    text is returned unchanged.
    """
    match = _ADDRESS_START_PATTERN.search(text)
    if match and match.start() > 0:
        return text[match.start():]
    return text


# Role-header phrasings where the entity name commonly follows ON THE SAME
# LINE ("MANUFACTURED BY: Hindustan Unilever Ltd.") rather than starting on
# the next line. Used to strip the header text and keep only the name.
ROLE_HEADER_PATTERN = re.compile(
    r"(?:manufactured\s*(?:in\s+[a-zA-Z\s]+)?\s*(?:&|and)?\s*(?:packed|marketed)?\s*by|"
    r"packed\s*(?:&|and)?\s*(?:marketed)?\s*by|"
    r"imported\s*(?:&|and)?\s*(?:marketed|packed)?\s*by|"
    r"marketed\s*by|"
    r"packer\s*[:\-]|importer\s*[:\-])\s*[:\-]?\s*",
    re.IGNORECASE,
)


def _classify_party_blocks(
    response: ExtractionResponse, lines: List[RawOCRLine], consumed_indices: set
) -> None:
    for i, line in enumerate(lines):
        if i in consumed_indices:
            continue
        roles = keywords.match_role_keyword(line.text)
        if not roles:
            continue

        # Some labels put the entity name on the SAME line as the header
        # ("MANUFACTURED BY: Hindustan Unilever Ltd."). Strip the header
        # text; whatever remains (if anything) is the name, and address
        # accumulation starts from the next line either way.
        same_line_name = ROLE_HEADER_PATTERN.sub("", line.text, count=1).strip()
        same_line_name = same_line_name if same_line_name and same_line_name != line.text else None

        block_lines = []
        for j in range(i + 1, min(i + 1 + ROLE_BLOCK_MAX_LINES, len(lines))):
            if j in consumed_indices:
                break
            candidate = lines[j]
            # Real labels often have a front-panel column (brand name,
            # tagline) sitting at a similar height to the back-panel
            # manufacturer/address column. Sorting by Y alone interleaves
            # them; skip anything that doesn't share the same column,
            # rather than blindly accumulating whatever comes next in reading order.
            if not _is_same_column(line, candidate):
                continue
            if keywords.is_consumer_care_line(candidate.text):
                break
            if regex.find_phones(candidate.text) or regex.find_email(candidate.text):
                break
            if keywords.match_role_keyword(candidate.text):
                break
            block_lines.append(candidate)
            if regex.find_pin_code(candidate.text):
                break  # PIN code line is typically the last address line
            if len(block_lines) >= 4:
                break  # enough address lines gathered; stop before drifting into unrelated content

        if not block_lines and not same_line_name:
            continue

        consumed_indices.add(i)
        for cand in block_lines:
            cand_idx = next((idx for idx, l in enumerate(lines) if l is cand), None)
            if cand_idx is not None:
                consumed_indices.add(cand_idx)

        if same_line_name:
            name = same_line_name
            address = (
                ", ".join(_clean_address_line(l.text) for l in block_lines)
                if block_lines else None
            )
            contributing = [line] + block_lines
        else:
            name = block_lines[0].text
            address = (
                ", ".join(_clean_address_line(l.text) for l in block_lines[1:])
                if len(block_lines) > 1 else None
            )
            contributing = [line] + block_lines

        avg_confidence = sum(l.confidence for l in contributing) / len(contributing)

        # Combined phrasing ("Manufactured & Packed by X") means the SAME
        # entity fills every listed role -- populate each applicable field
        # with identical party info rather than picking just one and
        # silently dropping the rest.
        combined_role_label = "/".join(roles)
        for role in roles:
            party = PartyInfo(
                name=name, address=address, role=combined_role_label, found=True, confidence=avg_confidence
            )
            if role == "manufacturer" and not response.manufacturer.found:
                response.manufacturer = party
            elif role == "packer" and not response.packer.found:
                response.packer = party
            elif role == "importer" and not response.importer.found:
                response.importer = party
            elif role == "marketer" and not response.manufacturer.found:
                response.manufacturer = party


import re as _re

# Raw lines to scan after (and including) the consumer care keyword before
# column-filtering. Needs to be generous because on two-column label layouts
# (e.g. Haldiram's) nutrition table rows from the adjacent column are
# interleaved with the consumer care rows in reading order, consuming the
# budget before reaching the phone/email line.  Column filtering removes those
# cross-column lines so only the consumer-care column lines count.
CONSUMER_CARE_RAW_WINDOW = 15

_BARCODE_SHAPE = _re.compile(r"^[\d\s\-]+$")


def _looks_like_barcode(text: str) -> bool:
    """UPC/EAN barcodes are digits-only (plus spaces/dashes) at standard
    lengths. A bare 10-13 digit run can otherwise look exactly like a phone
    number to a regex that only checks digit count."""
    if not _BARCODE_SHAPE.match(text.strip()):
        return False
    digit_count = len(_re.sub(r"\D", "", text))
    return digit_count in (8, 12, 13, 14)


def _classify_consumer_care(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    keyword_line: Optional[RawOCRLine] = None
    keyword_index: Optional[int] = None
    for i, l in enumerate(lines):
        if keywords.is_consumer_care_line(l.text):
            keyword_index = i
            keyword_line = l
            break

    if keyword_index is not None:
        # Take a generous raw slice, then keep only lines in the same column
        # as the keyword line. On multi-column layouts the reading-order sort
        # interleaves nutrition rows (different column) with consumer-care rows
        # at the same Y -- without the column filter those nutrition rows
        # exhaust the window budget before the phone / email line is reached.
        raw_window = lines[keyword_index : keyword_index + CONSUMER_CARE_RAW_WINDOW]
        search_lines = [
            l for l in raw_window
            if l is keyword_line or _is_same_column(keyword_line, l)
        ]
        has_keyword_context = True
    else:
        # No keyword found at all -- fall back to a full-document scan, but
        # flag it since we can't be sure this contact info is consumer care
        # and not something else (e.g. a manufacturer's own phone number).
        search_lines = lines
        has_keyword_context = False


    phones: List[str] = []
    email: Optional[str] = None
    contributing_lines: List[RawOCRLine] = []

    for line in search_lines:
        if _looks_like_barcode(line.text):
            continue
        found_phones = regex.find_phones(line.text)
        found_email = regex.find_email(line.text)
        if found_phones:
            phones.extend(found_phones)
            contributing_lines.append(line)
        if found_email and not email:
            email = found_email
            contributing_lines.append(line)

    if not phones and not email:
        return

    if not has_keyword_context:
        response.uncertainFields.append(
            "Phone/email found without a 'Customer Care' keyword nearby; "
            "assumed to be consumer care contact but not confirmed by context."
        )

    avg_confidence = (
        sum(l.confidence for l in contributing_lines) / len(contributing_lines)
        if contributing_lines else 0.0
    )

    response.consumerCare.phone = " | ".join(dict.fromkeys(phones)) or None  # dedupe, keep order
    response.consumerCare.email = email
    response.consumerCare.found = True
    response.consumerCare.confidence = avg_confidence
    if contributing_lines:
        response.consumerCare.bbox = contributing_lines[0].bbox


def _classify_qualifiers_and_misleading_terms(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    for line in lines:
        for hit in keywords.find_quantity_qualifiers(line.text):
            response.quantityQualifiers.append(
                QuantityQualifier(text=hit["text"], qualifierType=hit["qualifierType"], bbox=line.bbox)
            )
        for term in keywords.find_misleading_terms(line.text):
            response.misleadingQuantityTerms.append(MisleadingTerm(text=term, bbox=line.bbox))
