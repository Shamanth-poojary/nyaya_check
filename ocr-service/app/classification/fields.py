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

from app.classification import keywords, regex
from app.schemas.response import (
    BatchNumber,
    DateField,
    ExtractionResponse,
    MisleadingTerm,
    MRP,
    NetQuantity,
    PartyInfo,
    QuantityQualifier,
    RawOCRLine,
)

ROLE_BLOCK_MAX_LINES = 6

# Lines containing these should never be treated as a net-quantity candidate,
# even though they contain a number+unit -- they're a different field that
# happens to share the same shape (e.g. "USP :RS 0.07ML" is unit selling
# PRICE per ml, not the product's net quantity).
NET_QTY_EXCLUSION_KEYWORDS = ["usp", "unit selling price", "per unit", "mrp"]


def classify_fields(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    """Mutates `response` in place based on `lines` (response.rawOCR)."""
    ordered = sorted(lines, key=lambda l: l.bbox.ymin)

    consumed_indices: set = set()

    _classify_mrp(response, ordered)
    _classify_net_quantity(response, ordered)
    _classify_dates(response, ordered)
    _classify_batch_number(response, ordered)
    _classify_party_blocks(response, ordered, consumed_indices)
    _classify_consumer_care(response, ordered)
    _classify_qualifiers_and_misleading_terms(response, ordered)


def _classify_mrp(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    candidates = []
    for line in lines:
        hit = regex.find_mrp(line.text)
        if hit:
            value, tax_included = hit
            candidates.append((value, tax_included, line))

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
    # Prefer lines with an explicit "Net Qty"/"Net Wt" keyword.
    for line in lines:
        if keywords.is_net_quantity_line(line.text):
            hit = regex.find_net_quantity(line.text)
            if hit:
                response.netQuantity = NetQuantity(bbox=line.bbox, found=True, confidence=line.confidence, **hit)
                return

    # Fall back to a bare quantity+unit match, but never on excluded lines
    # (unit price, MRP, etc. share the same "number + unit" shape).
    for line in lines:
        lowered = line.text.lower()
        if any(k in lowered for k in NET_QTY_EXCLUSION_KEYWORDS):
            continue
        hit = regex.find_net_quantity(line.text)
        if hit:
            response.uncertainFields.append(
                f"Quantity '{hit['rawValue']}' found without a 'Net Qty' keyword nearby; "
                "not confident this is the declared net quantity -- left unclassified."
            )
            return  # don't guess further; one ambiguous note is enough


def _classify_dates(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    for line in lines:
        date_hit = regex.find_date(line.text)
        if not date_hit:
            continue
        date_type = keywords.match_date_type_keyword(line.text) or "manufacturing"

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
        elif date_type != "expiry" and not response.manufacturingDate.found:
            response.manufacturingDate = field


def _classify_batch_number(response: ExtractionResponse, lines: List[RawOCRLine]) -> None:
    for line in lines:
        batch = regex.find_batch_number(line.text)
        if batch:
            response.batchNumber = BatchNumber(
                value=batch, raw=line.text, bbox=line.bbox, found=True, confidence=line.confidence,
            )
            return


def _classify_party_blocks(
    response: ExtractionResponse, lines: List[RawOCRLine], consumed_indices: set
) -> None:
    for i, line in enumerate(lines):
        role = keywords.match_role_keyword(line.text)
        if not role:
            continue

        block_lines = []
        for j in range(i + 1, min(i + 1 + ROLE_BLOCK_MAX_LINES, len(lines))):
            candidate = lines[j]
            if keywords.is_consumer_care_line(candidate.text):
                break
            if regex.find_phones(candidate.text) or regex.find_email(candidate.text):
                break
            if keywords.match_role_keyword(candidate.text):
                break
            block_lines.append(candidate)
            if regex.find_pin_code(candidate.text):
                break  # PIN code line is typically the last address line

        if not block_lines:
            continue

        name = block_lines[0].text
        address = ", ".join(l.text for l in block_lines[1:]) if len(block_lines) > 1 else None
        avg_confidence = sum(l.confidence for l in [line] + block_lines) / (1 + len(block_lines))

        party = PartyInfo(
            name=name,
            address=address,
            role=role,
            found=True,
            confidence=avg_confidence,
        )

        # "Manufactured & Marketed by" etc. -- assign to manufacturer by
        # default since it's the more legally load-bearing mandatory field;
        # packer/importer only get their own explicit keywords.
        if role in ("manufacturer", "marketer") and not response.manufacturer.found:
            response.manufacturer = party
        elif role == "packer" and not response.packer.found:
            response.packer = party
        elif role == "importer" and not response.importer.found:
            response.importer = party


import re as _re

CONSUMER_CARE_WINDOW = 5  # lines to scan after (and including) a 'Customer Care' keyword line

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
    keyword_index = next((i for i, l in enumerate(lines) if keywords.is_consumer_care_line(l.text)), None)

    if keyword_index is not None:
        # Spatial reasoning: only look near the actual "Customer Care" label,
        # not the whole document -- otherwise unrelated digit strings
        # elsewhere (e.g. a barcode) can look like a phone number.
        search_lines = lines[keyword_index : keyword_index + CONSUMER_CARE_WINDOW]
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
