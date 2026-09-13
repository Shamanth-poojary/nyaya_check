"""
Classification tests using REAL rawOCR output captured from actual photos
(hana1.jpeg, hana3.jpeg) rather than clean synthetic text -- these fixtures
include the actual OCR noise/typos we've seen (HFD for MFD, Emait for
Email, etc.), so a pass here means the classifier tolerates real conditions.
"""

from app.classification.fields import classify_fields
from app.schemas.response import BoundingBox, ExtractionResponse, RawOCRLine, empty_response


def _line(text, xmin, ymin, xmax, ymax, confidence=0.95):
    return RawOCRLine(text=text, bbox=BoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax), confidence=confidence)


# Captured from hana1.jpeg (batch/date/price printed on clear plastic)
HANA1_LINES = [
    _line("B.NO:MNGMARDYI14", 255, 701, 476, 736, 0.939),
    _line("HFD :26/03/2026", 254, 725, 468, 764, 0.948),   # 'MFD' misread as 'HFD'
    _line("EXP :26 /09/2026", 258, 751, 481, 788, 0.939),
    _line("MRP :RS 40", 257, 776, 423, 817, 0.909),
    _line("USP :RS 0.07ML", 261, 804, 458, 837, 0.917),    # must NOT be read as net quantity
]

# Captured from hana2.jpeg (nutrition panel + ingredients + net contents)
HANA2_LINES = [
    _line("Ingredients:", 271, 382, 347, 400, 0.999),
    _line("Carbonated Water, Fresh Lemon", 210, 397, 402, 429, 0.869),
    _line("Sugar, Salt, Acidity Regulator", 224, 415, 391, 440, 0.915),  # 'Salt' here is an INGREDIENT, not the category
    _line("Nutritionalinformation", 226, 473, 338, 486, 0.979),
    _line("per100ml(ApproximateValue", 206, 480, 355, 501, 0.893),      # must NOT be read as net quantity
    _line("Per100ml", 359, 475, 410, 497, 0.965),
    _line("MRP:", 244, 635, 290, 657, 0.997),
    _line("Mfg. Date :", 244, 672, 312, 690, 0.969),
    _line("Batch No.:", 244, 691, 312, 710, 0.993),
    _line("Net Contents:", 226, 950, 407, 990, 0.985),   # keyword...
    _line("600 ml", 252, 978, 401, 1033, 0.978),          # ...and value on a SEPARATE physical line
    _line("Issal 11221331000187", 223, 719, 419, 762, 0.857),  # internal code, NOT a phone number
    _line("11222335000034", 292, 741, 421, 769, 0.9999),       # same -- another internal code
]


def test_hana2_internal_codes_not_misread_as_phone_numbers():
    """Regression test for a real bug found in a 4-photo test: hana2.jpeg
    has no 'Customer Care' keyword anywhere in its own text, so consumer
    care classification fell back to a full-document scan -- which matched
    a spurious 10-digit substring EMBEDDED inside a longer batch/expiry
    code ('Issal 11221331000187'), because the old phone regex only
    enforced a word boundary at the END of the match, not the start. This
    must produce nothing, not a false 'consumer care found' with a
    misleading uncertainFields note."""
    r = _classify(HANA2_LINES)
    assert r.consumerCare.found is False
    assert not any("Phone/email found" in note for note in r.uncertainFields)


# --- Real 6-product batch test (Everest, Dove, Haldiram's, Nandini, Bisleri, Tata Tea) ---
# Found: column-interleaved layouts (front-panel text at similar height to
# back-panel manufacturer text) corrupting party-block extraction; a
# same-line "MANUFACTURED BY: X" pattern my code didn't handle; a WRONG
# (not just missing) MRP value from a bad line-merge; and a reading-order
# bug where a value's bbox (e.g. a batch code's digits) sorted BEFORE its
# own keyword due to a slightly different box height.

def test_everest_manufacturer_not_polluted_by_front_panel_column():
    """'Turmeric'/'Powder' are big front-panel brand text at a similar
    height to the back-panel manufacturer block, but a different column.
    Naive Y-only sorting swept them into the manufacturer's address."""
    lines = [
        _line("MANUFACTURED & PACKED BY:", 286, 161, 433, 174),
        _line("EVEREST", 50, 159, 194, 198),
        _line("Everest Food Products Pvt. Ltd.", 286, 173, 430, 186),
        _line("4/B, LB.S. Marg, Vikhroli (W).", 284, 183, 415, 198),
        _line("Turmeric", 63, 209, 179, 237),
        _line("Mumbai - 400 083, Maharashtra, India.", 285, 197, 455, 210),
        _line("Powder", 70, 236, 172, 270),
    ]
    r = _classify(lines)
    assert r.manufacturer.name == "Everest Food Products Pvt. Ltd."
    assert "Turmeric" not in (r.manufacturer.address or "")
    assert "Powder" not in (r.manufacturer.address or "")


def test_haldirams_manufacturer_name_not_the_ingredients_header():
    """'INGREDIENTS:' and 'MANUFACTURED & PACKED BY:' sit on the same
    physical row in two side-by-side columns; naive sorting picked
    'INGREDIENTS:' as the manufacturer NAME."""
    lines = [
        _line("INGREDIENTS:", 328, 54, 395, 66),
        _line("MANUFACTURED & PACKED BY:", 522, 53, 681, 67),
        _line("Potato (62%). Edible Vegetable Oil (Palmolein).", 326, 68, 516, 82),
        _line("Heldiram Foods International Ltd.", 521, 68, 671, 82),
    ]
    r = _classify(lines)
    assert r.manufacturer.name != "INGREDIENTS:"
    assert "Heldiram Foods" in r.manufacturer.name


def test_dove_same_line_manufacturer_name_extracted_correctly():
    """'MANUFACTURED BY: Hindustan Unilever Ltd.' puts the name on the SAME
    line as the header -- the old code always deferred to the next line,
    incorrectly grabbing unrelated front-panel text ('Intense') instead."""
    lines = [
        _line("MANUFACTURED BY: Hiodustan Unilever Ltd.", 238, 168, 380, 181),
        _line("Intense", 64, 176, 127, 196),
        _line("Uni-J, Piet No. 1. Sector 1A.", 237, 179, 334, 192),
    ]
    r = _classify(lines)
    assert r.manufacturer.name == "Hiodustan Unilever Ltd."
    assert r.manufacturer.name != "Intense"


def test_dove_mrp_not_the_net_volume_value():
    """Real, serious bug: a bad line-merge combined 'MRPZ' with ':180 ml'
    (a net volume from a nearby but distinct label), and naive first-number
    extraction returned 180 as the PRICE. The real price (199.00) is on a
    separate line. This must find 199, not silently return a wrong value."""
    lines = [
        _line("Net Vol.", 224, 346, 263, 364),
        _line("MRPZ :180 ml", 224, 349, 317, 384),
        _line(": 199.00", 275, 375, 316, 386),
    ]
    r = _classify(lines)
    assert r.mrp.found is True
    assert r.mrp.value == 199.0


def test_nandini_mrp_found_when_keyword_and_amount_narrowly_miss_merging():
    """'MRP' and '(incl. of all taxes) :67.00' have overlapping bboxes that
    fall just outside the line-merge threshold -- must still find the
    amount via windowed search, not silently return not-found."""
    lines = [
        _line("MANUFACTURED BY:", 298, 280, 387, 295),
        _line("LONG LIFE", 96, 283, 176, 300),  # front-panel text, wrong column
        _line("Kamataka Co-operative Milk", 299, 294, 413, 306),
        _line("MRP", 303, 169, 340, 187),
        _line("(incl. of all taxes) :67.00", 303, 169, 417, 201),
    ]
    r = _classify(lines)
    assert r.mrp.found is True
    assert r.mrp.value == 67.0
    assert r.manufacturer.name != "LONG LIFE"


def test_bisleri_batch_number_found_despite_value_sorting_before_keyword():
    """'B0724's bbox starts 2px higher than 'Batch No.'s bbox (digit vs
    letter height), which flips their order under naive ymin-only sorting
    -- the windowed search only looks FORWARD, so it silently missed the
    value entirely. Reading order must be robust to this."""
    lines = [
        _line("Bisleri MRP", 8, 211, 200, 281),
        _line("(ncl. of all taxes) 20.00", 167, 230, 282, 261),
        _line("Batch No.", 168, 263, 208, 278),
        _line("B0724", 249, 261, 286, 276),
    ]
    r = _classify(lines)
    assert r.batchNumber.found is True
    assert r.batchNumber.value == "B0724"
    assert r.mrp.found is True
    assert r.mrp.value == 20.0


# --- Second real-photo batch: same 6 products re-tested after the first
# round of fixes. Found three MORE real bugs -- a wrong value from a
# glued-digit OCR artifact, a regression in the MRP windowed search
# itself, and dates defaulting to the wrong type when their keyword sits
# on the line ABOVE rather than the same line.

def test_everest_mrp_not_a_glued_digit_artifact():
    """Real bug: OCR read the MRP label as 'MRP7' -- a stray '7' fused
    directly onto the keyword with zero separator. The real price (60.00)
    is on a separate, adjacent line. A digit glued straight onto 'MRP'
    with no space/colon/currency-symbol is virtually always OCR noise,
    not an actual price."""
    lines = [
        _line("MRP7", 288, 338, 323, 353),
        _line("60.00", 379, 341, 413, 355),
    ]
    r = _classify(lines)
    assert r.mrp.found is True
    assert r.mrp.value == 60.0


def test_dove_mrp_windowed_search_skips_low_confidence_garbage():
    """Regression test for a bug introduced by the MRP windowed-search fix
    itself: a low-confidence garbled fragment ('E800 I', confidence 0.30)
    sat closer in reading order than the real value (': 199.00', confidence
    0.93), and taking the FIRST window candidate grabbed the garbage. Must
    prefer the highest-confidence candidate in the window, not the first."""
    lines = [
        _line("MRPZ :180 ml", 224, 349, 317, 384),
        _line("E800 I", 376, 349, 387, 385, confidence=0.30),
        _line(": 199.00", 275, 375, 316, 386, confidence=0.93),
    ]
    r = _classify(lines)
    assert r.mrp.found is True
    assert r.mrp.value == 199.0


def test_everest_expiry_date_keyword_on_preceding_line():
    """'Use By' sits on its own line, with the date itself on the NEXT
    line -- the date classifier only checked the date's own line for a
    keyword, silently defaulting to 'manufacturing' even with 'Use By'
    sitting immediately above it."""
    lines = [
        _line("Use By", 285, 398, 323, 419),
        _line("11 JUL 2025", 380, 402, 442, 416),
    ]
    r = _classify(lines)
    assert r.expiryDate.found is True
    assert r.expiryDate.month == 7 and r.expiryDate.year == 2025
    assert r.manufacturingDate.found is False


def test_bisleri_expiry_date_keyword_merged_with_front_panel_text():
    """Same preceding-line-keyword pattern, complicated by column
    interleaving: 'Use By' got merged with unrelated front-panel tagline
    text ('since 1969') into one garbled line, but the keyword is still
    present as a substring and must still be found."""
    lines = [
        _line("since 1969 11 Use By", 42, 301, 198, 324),
        _line("04 JUL 2025", 249, 299, 313, 313),
    ]
    r = _classify(lines)
    assert r.expiryDate.found is True
    assert r.expiryDate.month == 7 and r.expiryDate.year == 2025
    assert r.manufacturingDate.found is False


def test_hana2_net_quantity_found_across_separate_lines():
    """Regression test for a real bug found in a 4-photo test: 'Net
    Contents:' and '600 ml' sit on two separate physical lines (not a
    split-detection artifact -- a genuine two-line label layout). The
    classifier must search nearby lines, not just the same line, AND must
    not get shadowed by the nutrition panel's 'per100ml' reference, which
    appears earlier in reading order and matches the same number+unit shape."""
    r = _classify(HANA2_LINES)
    assert r.netQuantity.found is True
    assert r.netQuantity.value == 600.0
    assert r.netQuantity.normalizedUnit == "ml"


def test_hana2_ingredient_list_not_misread_as_commodity_category():
    """Regression test for a real bug: 'Sugar, Salt, Acidity Regulator' is
    an INGREDIENT list, not the product's category. Naive whole-document
    keyword matching classified this as category='Salt', which is wrong
    for any product (a huge fraction of packaged foods list salt/sugar as
    ingredients regardless of what the product actually is)."""
    r = _classify(HANA2_LINES)
    assert r.commodity.category != "Salt"


# --- Aashirvaad Superior MP Atta (5 kg) regression tests ---
#
# Real failure mode confirmed on a real photo:
# 1. 'MP' from 'SUPERIOR MP ATTA' (the product's own name) fuzzy-matched
#    'MRP' (edit distance 1, both within the old length-diff tolerance of 1).
# 2. That triggered is_mrp_line → windowed search.
# 3. The windowed search found '77' from "Survey No. 77, 78, 79" in the
#    manufacturer's address, which beat the real MRP line (₹295.00) on
#    OCR confidence, returning a completely wrong price.
#
# These fixtures reproduce the OCR output from the back-of-pack label.
# Bboxes are illustrative (right-column table region for the info block,
# left region for the manufacturer address text that contains the survey numbers).
AASHIRVAAD_LINES = [
    # Front-panel product name — contains 'MP' which must NOT match 'MRP'
    _line("AASHIRVAAD", 50, 80, 400, 140, 0.99),
    _line("SUPERIOR MP ATTA", 50, 145, 420, 200, 0.98),
    _line("WHOLE WHEAT FLOUR", 50, 205, 400, 240, 0.96),
    # Manufacturer address block (back panel, left column)
    # Contains survey numbers -- these must NEVER be mistaken for the MRP
    _line("MANUFACTURED & PACKED BY:", 510, 80, 820, 100, 0.99),
    _line("ITC Limited - Foods Division,", 510, 105, 820, 125, 0.97),
    _line("Survey No. 77, 78, 79, Village: Mettupalayam,", 510, 130, 820, 150, 0.95),
    _line("Taluk: Coimbatore - 641 301, Tamil Nadu, India.", 510, 155, 820, 175, 0.96),
    # Ingredients
    _line("INGREDIENTS:", 510, 185, 820, 200, 0.99),
    _line("Whole Wheat", 510, 205, 820, 220, 0.98),
    # Structured info table (back panel, bottom-right)
    _line("Net Weight   : 5 kg", 510, 430, 820, 455, 0.98),
    _line("MRP Rs       : 295.00", 510, 460, 820, 485, 0.97),
    _line("(incl. of all taxes)", 510, 488, 820, 505, 0.95),
    _line("Batch No.    : A4G0724", 510, 510, 820, 530, 0.96),
    _line("Date of Packaging : 15 JUL 2024", 510, 535, 820, 555, 0.97),
    _line("Use By       : 14 JAN 2025", 510, 560, 820, 578, 0.97),
]


def test_aashirvaad_mrp_not_address_number():
    """Core regression: MRP must be 295.00 (from the info table), not 77, 78,
    or 79 from the manufacturer's 'Survey No. 77, 78, 79' address line.
    The old code fuzzy-matched 'MP' in 'SUPERIOR MP ATTA' as 'MRP', triggered
    a windowed search that grabbed 77 from the address, and returned a
    completely wrong price."""
    r = _classify(AASHIRVAAD_LINES)
    assert r.mrp.found is True
    assert r.mrp.value == 295.0, (
        f"Expected MRP=295.0 but got {r.mrp.value} -- "
        "'MP' in product name must not fuzzy-match 'MRP'"
    )


def test_aashirvaad_batch_number_found():
    """Batch number A4G0724 must be extracted correctly from 'Batch No. : A4G0724'
    on the structured back-panel table."""
    r = _classify(AASHIRVAAD_LINES)
    assert r.batchNumber.found is True
    assert r.batchNumber.value == "A4G0724", (
        f"Expected batchNumber='A4G0724' but got {r.batchNumber.value!r}"
    )


def test_aashirvaad_mp_not_fuzzy_matched_as_mrp_keyword():
    """Unit-level guard: 'SUPERIOR MP ATTA' alone (no MRP value present)
    must NOT trigger is_mrp_line. If it does, the windowed search that
    follows will grab the nearest number (the survey address) as the price."""
    from app.classification.regex import is_mrp_line
    assert not is_mrp_line("SUPERIOR MP ATTA"), (
        "'MP' in a product name is not an MRP keyword -- "
        "is_mrp_line must return False for this input"
    )


def test_aashirvaad_expiry_date_found():
    """'Use By : 14 JAN 2025' must be classified as expiry date."""
    r = _classify(AASHIRVAAD_LINES)
    assert r.expiryDate.found is True
    assert r.expiryDate.day == 14
    assert r.expiryDate.month == 1
    assert r.expiryDate.year == 2025


def test_aashirvaad_packing_date_found():
    """'Date of Packaging : 15 JUL 2024' must be classified as packing date."""
    r = _classify(AASHIRVAAD_LINES)
    assert r.packingDate.found is True
    assert r.packingDate.day == 15
    assert r.packingDate.month == 7
    assert r.packingDate.year == 2024

HANA3_LINES = [
    _line("TEAR HERE AND", 223, 195, 302, 215, 0.99),
    _line("FIND THE CODE", 223, 208, 298, 223, 0.97),
    _line("hana", 188, 315, 369, 401, 0.98),
    _line("Manufactured & Marketed by", 176, 411, 371, 432, 0.99),
    _line("Swadeshi Food & Beverages", 175, 423, 360, 449, 0.95),
    _line("NO.G5-334/1Shamn Comon", 173, 435, 433, 472, 0.60),
    _line(" A Cross,Kanaka Nagar.RT Nagar Post", 175, 454, 428, 485, 0.80),
    _line("560032 Bengaluru, Karnataka,india", 180, 475, 403, 495, 0.97),
    _line("Customer Care No:", 182, 505, 305, 526, 0.98),
    _line(" +91 98444 88117|+91 98444 87302", 179, 517, 414, 545, 0.95),
    _line("Emait: swadeshifb@gmail.com", 180, 534, 379, 559, 0.98),  # 'Email' misread as 'Emait'
    _line("www.hanadrinks.in", 183, 553, 307, 573, 0.99),
    _line("8 906095260584", 197, 637, 383, 666, 0.95),
    _line("Product of", 273, 790, 326, 808, 0.96),
    _line("INDIA", 271, 801, 335, 827, 0.99),
]


def _classify(lines):
    response = empty_response("test.jpg", 720, 1280)
    response.rawOCR = lines
    classify_fields(response, lines)
    return response


def test_hana1_mrp():
    r = _classify(HANA1_LINES)
    assert r.mrp.found is True
    assert r.mrp.value == 40.0


def test_hana1_manufacturing_date_tolerates_hfd_misread():
    r = _classify(HANA1_LINES)
    assert r.manufacturingDate.found is True
    assert r.manufacturingDate.month == 3
    assert r.manufacturingDate.year == 2026


def test_hana1_expiry_date():
    r = _classify(HANA1_LINES)
    assert r.expiryDate.found is True
    assert r.expiryDate.month == 9
    assert r.expiryDate.year == 2026


def test_hana1_batch_number():
    r = _classify(HANA1_LINES)
    assert r.batchNumber.found is True
    assert r.batchNumber.value == "MNGMARDYI14"


def test_hana1_usp_not_misread_as_net_quantity():
    """USP (unit selling price per ml) must NOT be classified as net quantity --
    they share the same 'number + unit' shape but mean different things."""
    r = _classify(HANA1_LINES)
    assert r.netQuantity.found is False


def test_hana3_manufacturer_name_and_address():
    r = _classify(HANA3_LINES)
    assert r.manufacturer.found is True
    assert r.manufacturer.name == "Swadeshi Food & Beverages"
    assert "560032 Bengaluru" in r.manufacturer.address
    assert "Cross" in r.manufacturer.address


def test_hana3_commodity_category_from_indirect_signal():
    """No photo has an explicit 'product type' label -- category has to be
    inferred from indirect signal: 'Swadeshi Food & Beverages' (manufacturer
    name) and 'hanadrinks.in' (website). This is exactly the scenario
    strict word-boundary keyword matching broke on (plurals, concatenated
    text) before being fixed."""
    r = _classify(HANA3_LINES)
    assert r.commodity.found is True
    assert r.commodity.category == "Beverage"


def test_hana1_no_false_positive_commodity_category():
    """hana1's text is pure batch/date/price data -- no category signal
    should be manufactured out of nothing."""
    r = _classify(HANA1_LINES)
    assert r.commodity.found is False


def test_commodity_short_keyword_avoids_false_substring_match():
    """'tea' must not match inside unrelated words like 'instead' --
    regression guard for the word-boundary vs substring matching split."""
    from app.classification.commodity import classify_commodity
    assert classify_commodity("please read the label instead of guessing") is None


def test_hana3_consumer_care_phone_and_email():
    r = _classify(HANA3_LINES)
    assert r.consumerCare.found is True
    assert "98444 88117" in r.consumerCare.phone
    assert "98444 87302" in r.consumerCare.phone
    assert r.consumerCare.email == "swadeshifb@gmail.com"  # correct despite 'Emait' typo on the label


def test_hana3_barcode_not_misread_as_phone_number():
    """The barcode line ('8 906095260584') is far below the Customer Care
    block and must NOT be swept up as a third phone number just because it
    happens to contain 10 consecutive digits."""
    r = _classify(HANA3_LINES)
    phone_numbers = r.consumerCare.phone.split(" | ")
    assert len(phone_numbers) == 2
    assert not any("6095260584" in p for p in phone_numbers)


def test_split_lines_are_merged_before_classification():
    """Regression test for a real bug: with CLAHE preprocessing on,
    PaddleOCR split 'MRP :RS 40' into 'MRE' + ':RS 40' (and similarly for
    HFD/EXF date lines), which broke MRP and expiry-date classification
    entirely since keyword and value ended up on different lines. This
    reproduces those exact split detections and confirms merge_split_lines
    (Phase 4) repairs them before the classifier ever sees the data."""
    from app.ocr.normalize import merge_split_lines
    from app.ocr.paddle import OCRLine

    split_lines = [
        OCRLine(text="B.NO:MNGMARDYI!4", bbox=(254, 701, 472, 737), confidence=0.92),
        OCRLine(text="HFD", bbox=(259, 734, 306, 762), confidence=0.97),
        OCRLine(text=":26/03/2026", bbox=(310, 728, 466, 759), confidence=0.99),
        OCRLine(text="EXF", bbox=(258, 753, 310, 790), confidence=0.88),
        OCRLine(text=":26 /09/2026", bbox=(306, 752, 482, 787), confidence=0.94),
        OCRLine(text="MRE", bbox=(261, 783, 308, 815), confidence=0.81),
        OCRLine(text=":RS 40", bbox=(303, 779, 422, 809), confidence=0.95),
    ]

    merged = merge_split_lines(split_lines)
    rec_lines = [
        _line(m.text, m.bbox[0], m.bbox[1], m.bbox[2], m.bbox[3], m.confidence) for m in merged
    ]
    r = _classify(rec_lines)

    assert r.mrp.found is True
    assert r.mrp.value == 40.0
    assert r.manufacturingDate.found is True
    assert r.manufacturingDate.month == 3
    assert r.expiryDate.found is True
    assert r.expiryDate.month == 9


def test_multi_image_merge_combines_complementary_photos():
    """The actual point of multi-image extraction: hana1.jpeg (batch/dates/
    MRP, photographed on the bottle body) and hana3.jpeg (manufacturer/
    consumer care, photographed on the back label) are TWO REAL PHOTOS OF
    THE SAME PRODUCT. Neither photo alone has everything Rule 6 requires;
    merged, the result should."""
    from app.classification.merge import merge_extraction_results
    from app.pipeline import _tag_source_image
    from app.schemas.response import empty_response

    hana1_response = empty_response("hana1.jpeg", 720, 1280)
    for l in HANA1_LINES:
        l.sourceImage = "hana1.jpeg"
    hana1_response.rawOCR = HANA1_LINES
    classify_fields(hana1_response, HANA1_LINES)
    _tag_source_image(hana1_response, "hana1.jpeg")

    hana3_response = empty_response("hana3.jpeg", 720, 1280)
    for l in HANA3_LINES:
        l.sourceImage = "hana3.jpeg"
    hana3_response.rawOCR = HANA3_LINES
    classify_fields(hana3_response, HANA3_LINES)
    _tag_source_image(hana3_response, "hana3.jpeg")

    merged = merge_extraction_results([hana1_response, hana3_response])

    # Fields only visible in hana1 survive the merge
    assert merged.mrp.found is True
    assert merged.mrp.value == 40.0
    assert merged.batchNumber.found is True

    # Fields only visible in hana3 ALSO survive the merge (this is the
    # actual value proposition -- neither single photo has both)
    assert merged.manufacturer.found is True
    assert merged.manufacturer.name == "Swadeshi Food & Beverages"
    assert merged.consumerCare.found is True
    assert merged.consumerCare.email == "swadeshifb@gmail.com"

    # Traceability: evidence is tagged with which photo it came from
    assert merged.mrp.sourceImage == "hana1.jpeg"
    assert merged.manufacturer.sourceImage == "hana3.jpeg"
    assert len(merged.sourceDocuments) == 2

    # Raw evidence from BOTH photos is preserved, not overwritten
    assert len(merged.rawOCR) == len(HANA1_LINES) + len(HANA3_LINES)

    # Still correctly not found anywhere (neither photo shows it) --
    # merging shouldn't manufacture a field that's genuinely absent
    assert merged.netQuantity.found is False


def test_multi_image_merge_flags_genuine_conflicts():
    """If two photos disagree on a fact that should be consistent (e.g.
    different MRP values), that must be flagged, not silently resolved --
    could mean two different products got mixed into one upload."""
    from app.classification.merge import merge_extraction_results
    from app.schemas.response import empty_response

    photo_a = empty_response("a.jpg", 720, 1280)
    photo_a.rawOCR = [_line("MRP :RS 40", 100, 100, 200, 130, 0.95)]
    classify_fields(photo_a, photo_a.rawOCR)

    photo_b = empty_response("b.jpg", 720, 1280)
    photo_b.rawOCR = [_line("MRP :RS 45", 100, 100, 200, 130, 0.90)]
    classify_fields(photo_b, photo_b.rawOCR)

    merged = merge_extraction_results([photo_a, photo_b])

    assert merged.mrp.value == 40.0  # higher confidence wins
    assert any("Conflicting" in note and "mrp" in note for note in merged.uncertainFields)


# ============================================================================
# Multi-product audit: Bisleri, Dove, Tata Tea, Nandini, Haldiram's
# ============================================================================
#
# Fixtures reproduce OCR-realistic text from the back-panel photos.
# Bboxes are illustrative but geometrically consistent with single-column
# right-panel layouts. Each fixture exercises at least one of the 4 bugs
# identified in the September 2026 multi-product audit.
#
# Bug 1: "use before" (Dove) not in EXPIRY_DATE_KEYWORDS  → wrong date type
# Bug 2: 11-digit toll-free phones (1800 + 7 digits) not matched by 5+5 pattern
# Bug 3: Spaced PIN codes ("560 029") not detected → address accumulation drifts
# Bug 4: Missing Dairy commodity category; Snacks missing bhujia/savoury

# ---------------------------------------------------------------------------
# Bisleri International Pvt. Ltd. — 1L Packaged Drinking Water
# Real consumer-care phone: 1800 121 1007 (toll-free, 4+3+4 format)
# ---------------------------------------------------------------------------
BISLERI_LINES = [
    _line("PACKAGED DRINKING WATER", 50, 50, 500, 75, 0.99),
    _line("INGREDIENTS: Treated Water, Minerals", 50, 90, 500, 110, 0.97),
    _line("(Calcium, Magnesium, Potassium)", 50, 112, 500, 130, 0.96),
    _line("Net Quantity: 1 L", 50, 200, 500, 225, 0.99),
    _line("MRP Rs  : 20.00", 50, 228, 500, 253, 0.98),
    _line("(incl. of all taxes)", 50, 255, 500, 275, 0.96),
    _line("Batch No. B0724", 50, 278, 500, 303, 0.97),
    _line("Date of Packaging : 05 JUL 2024", 50, 306, 500, 328, 0.98),
    _line("Use By : 04 JUL 2025", 50, 332, 500, 352, 0.97),
    _line("MANUFACTURED BY:", 50, 410, 500, 430, 0.99),
    _line("Bisleri International Pvt. Ltd.", 50, 432, 500, 452, 0.98),
    _line("Plot No. 7, MIDC, Hingna,", 50, 454, 500, 474, 0.97),
    _line("Nagpur - 440016, Maharashtra, India.", 50, 476, 500, 496, 0.96),
    _line("For consumer complaints contact:", 50, 520, 500, 540, 0.99),
    _line("Bisleri@bisleri.co.in | Ph: 1800 121 1007", 50, 542, 500, 562, 0.97),
    _line("www.bisleri.com", 50, 564, 500, 584, 0.96),
]

# ---------------------------------------------------------------------------
# Dove Intense Repair Shampoo — 180 ml
# Bug 1: "Use Before" must be expiry (not manufacturing)
# Bug 2: Toll-free "1800 10 22 221" (4+2+2+3 format)
# ---------------------------------------------------------------------------
DOVE_LINES = [
    _line("Dove Intense Repair Shampoo", 50, 50, 500, 72, 0.99),
    _line("INGREDIENTS: Water, Sodium Laureth Sulfate,", 50, 90, 500, 110, 0.97),
    _line("Dimethicone, Cocamidopropyl Betaine,", 50, 112, 500, 130, 0.96),
    _line("Glycerin, Fragrance, Glycol Distearate.", 50, 132, 500, 150, 0.95),
    _line("MANUFACTURED BY: Hindustan Unilever Ltd.", 50, 200, 500, 218, 0.99),
    _line("Unit-9, Plot No. 1, Sector 1A,", 50, 220, 500, 238, 0.97),
    _line("Haridwar - 249 403, Uttarakhand, India.", 50, 240, 500, 258, 0.96),
    _line("FOR CONSUMER COMPLAINTS / FEEDBACK:", 50, 300, 500, 320, 0.99),
    _line("Toll Free: 1800 10 22 221", 50, 322, 500, 342, 0.98),
    _line("Email: lever.care@unilever.com", 50, 344, 500, 364, 0.98),
    _line("Visit: www.dove.in", 50, 366, 500, 386, 0.96),
    _line("Net Vol.  : 180 ml", 50, 430, 500, 455, 0.99),
    _line("MRP Rs    : 199.00", 50, 458, 500, 480, 0.97),
    _line("(incl. of all taxes)", 50, 483, 500, 500, 0.96),
    _line("Batch No. : D0724", 50, 505, 500, 525, 0.97),
    _line("Mfg. Date : 05 JUL 2024", 50, 528, 500, 548, 0.98),
    _line("Use Before : 04 JUL 2025", 50, 551, 500, 571, 0.97),  # Bug 1 trigger
]

# ---------------------------------------------------------------------------
# Tata Tea Premium — 250 g
# Bug 2: Toll-free "1800 345 1720" (4+3+4 format)
# ---------------------------------------------------------------------------
TATA_TEA_LINES = [
    _line("TATA TEA PREMIUM", 50, 50, 500, 72, 0.99),
    _line("DESH KI CHAI", 50, 75, 500, 95, 0.98),
    _line("INGREDIENTS: Tea", 50, 130, 500, 150, 0.99),
    _line("MANUFACTURED & PACKED BY:", 50, 180, 500, 200, 0.99),
    _line("Tata Consumer Products Limited", 50, 202, 500, 222, 0.98),
    _line("1, Bishop Lefroy Road, Kolkata - 700 020,", 50, 224, 500, 244, 0.97),
    _line("West Bengal, India.", 50, 246, 500, 266, 0.96),
    _line("FOR CONSUMER COMPLAINTS / FEEDBACK:", 50, 300, 500, 320, 0.99),
    _line("Tata Consumer Care", 50, 322, 500, 342, 0.98),
    _line("Toll Free: 1800 345 1720", 50, 344, 500, 364, 0.98),
    _line("Email: care@tataconsumer.com", 50, 366, 500, 386, 0.98),
    _line("Net Weight    : 250 g", 50, 430, 500, 455, 0.99),
    _line("MRP Rs        : 275.00", 50, 458, 500, 480, 0.98),
    _line("(incl. of all taxes)", 50, 483, 500, 500, 0.96),
    _line("Batch No.     : T0724", 50, 505, 500, 525, 0.97),
    _line("Date of Packaging : 08 JUL 2024", 50, 528, 500, 548, 0.98),
    _line("Use By        : 07 JUL 2025", 50, 551, 500, 571, 0.97),
]

# ---------------------------------------------------------------------------
# Nandini Toned Milk — 1 L UHT
# Bug 2: Toll-free "1800 425 8030" (4+3+4)
# Bug 3: Spaced PIN "560 029" in manufacturer address
# Bug 4: commodity = Dairy (no category at all before fix)
# ---------------------------------------------------------------------------
NANDINI_LINES = [
    _line("TONED MILK", 50, 50, 500, 72, 0.99),
    _line("UHT PROCESSED", 50, 75, 500, 95, 0.98),
    _line("Net Quantity:  1 L", 50, 150, 500, 175, 0.99),
    _line("MRP Rs  : 67.00", 50, 178, 500, 200, 0.98),
    _line("(incl. of all taxes)", 50, 203, 500, 220, 0.96),
    _line("Batch No.  : T0724", 50, 225, 500, 245, 0.97),
    _line("Date of Packaging : 10 JUL 2024", 50, 248, 500, 268, 0.98),
    _line("Use By     : 09 JAN 2025", 50, 271, 500, 291, 0.97),
    _line("MANUFACTURED BY:", 50, 340, 500, 360, 0.99),
    _line("Karnataka Co-operative Milk Producers' Federation Ltd.", 50, 362, 500, 382, 0.97),
    # Spaced PIN "560 029" -- the stop-signal fix target (Bug 3)
    _line("KMF Nandini Dairy, Bengaluru - 560 029, Karnataka, India.", 50, 384, 500, 404, 0.96),
    # This line should NOT appear in the manufacturer address after the PIN fix
    _line("Lic. No. 10012043000053", 50, 406, 500, 426, 0.95),
    _line("FOR CONSUMER COMPLAINTS / FEEDBACK:", 50, 450, 500, 470, 0.99),
    _line("Ph: 1800 425 8030 (Toll Free)", 50, 472, 500, 492, 0.98),
    _line("Email: customercare@kmf.coop", 50, 494, 500, 514, 0.98),
]

# ---------------------------------------------------------------------------
# Haldiram's Aloo Bhujia — 200 g
# Bug 2: STD landline "+91-120-2400286"
# Bug 4: commodity = Snacks (bhujia keyword)
# ---------------------------------------------------------------------------
HALDIRAMS_LINES = [
    _line("Haldiram's", 50, 50, 500, 75, 0.99),
    _line("ALOO BHUJIA", 50, 78, 500, 110, 0.99),
    _line("RELISH THE GOODNESS OF DELIGHTFUL SAVOURY TREATS", 50, 112, 500, 132, 0.97),
    _line("INDIAN SNACKS", 50, 145, 200, 175, 0.97),  # decorative badge
    _line("INGREDIENTS:", 300, 145, 700, 165, 0.99),
    _line("Potato (62%). Edible Vegetable Oil (Palmolein).", 300, 168, 700, 186, 0.96),
    _line("Gram Flour (Besan), Iodised Salt, Spices &", 300, 188, 700, 206, 0.95),
    _line("Condiments (Chilli, Black Pepper, Clove,", 300, 208, 700, 226, 0.95),
    _line("Cardamom), Acidity Regulator (INS 330).", 300, 228, 700, 246, 0.94),
    _line("MANUFACTURED & PACKED BY:", 550, 280, 900, 300, 0.99),
    _line("Haldiram Foods International Ltd.", 550, 302, 900, 322, 0.98),
    _line("Plot No. 145, Sector 63,", 550, 324, 900, 344, 0.97),
    _line("Noida - 201307, Uttar Pradesh, India", 550, 346, 900, 366, 0.96),
    _line("FOR CONSUMER COMPLAINTS / FEEDBACK:", 550, 400, 900, 420, 0.99),
    _line("call us at +91-120-2400286", 550, 422, 900, 442, 0.98),  # STD landline
    _line("or email at customercare@haldiram.com", 550, 444, 900, 464, 0.98),
    _line("NET WEIGHT   : 200 g", 50, 530, 900, 555, 0.99),
    _line("MRP Rs       : 60.00", 50, 558, 900, 580, 0.98),
    _line("(incl. of all taxes)", 50, 583, 900, 600, 0.96),
    _line("BATCH NO.    : AB0724", 50, 605, 900, 625, 0.97),
    _line("DATE OF PACKAGING : 15 JUL 2024", 50, 628, 900, 648, 0.98),
    _line("USE BY       : 14 NOV 2024", 50, 651, 900, 671, 0.97),
]


# --- Bug 1 tests: "Use Before" as expiry date --------------------------------

def test_dove_use_before_classified_as_expiry():
    """'Use Before' is a synonym for 'Use By'/'Best Before' but was NOT in
    EXPIRY_DATE_KEYWORDS. Dove uses exactly this phrasing; before the fix it
    defaulted to manufacturing date -- wrong field AND wrong type."""
    r = _classify(DOVE_LINES)
    assert r.expiryDate.found is True, "Dove expiry date must be found"
    assert r.expiryDate.day == 4
    assert r.expiryDate.month == 7
    assert r.expiryDate.year == 2025
    assert r.manufacturingDate.found is True, "Mfg date (05 JUL 2024) must still be found"
    assert r.manufacturingDate.month == 7 and r.manufacturingDate.year == 2024


def test_dove_mfg_date_not_overwritten_by_use_before():
    """Confirming Mfg. Date and Use Before are classified into separate fields,
    not both collapsed into manufacturingDate (the pre-fix behaviour)."""
    r = _classify(DOVE_LINES)
    # manufacturing date: 05 JUL 2024
    assert r.manufacturingDate.found is True
    assert r.manufacturingDate.day == 5 and r.manufacturingDate.year == 2024
    # expiry: 04 JUL 2025 -- different year
    assert r.expiryDate.found is True
    assert r.expiryDate.year == 2025


# --- Bug 2 tests: toll-free and STD landline phone extraction ----------------

def test_bisleri_tollfree_phone_1800_4x3x4_extracted():
    """'1800 121 1007' is a real 11-digit Indian toll-free number in 4+3+4
    format. The old 5+5-only pattern could never match it."""
    r = _classify(BISLERI_LINES)
    assert r.consumerCare.found is True
    assert r.consumerCare.phone is not None
    assert "1800 121 1007" in r.consumerCare.phone, (
        f"Expected toll-free 1800 121 1007 in phone, got: {r.consumerCare.phone!r}"
    )


def test_dove_tollfree_phone_1800_4x2x2x3_extracted():
    """'1800 10 22 221' is a real toll-free number in an unusual 4+2+2+3
    grouping -- most challenging for the pattern since it's not 3+4."""
    r = _classify(DOVE_LINES)
    assert r.consumerCare.found is True
    assert r.consumerCare.phone is not None
    assert "1800 10 22 221" in r.consumerCare.phone, (
        f"Expected 1800 10 22 221 in phone, got: {r.consumerCare.phone!r}"
    )


def test_tata_tea_tollfree_phone_extracted():
    """'1800 345 1720' — standard 4+3+4 toll-free format."""
    r = _classify(TATA_TEA_LINES)
    assert r.consumerCare.found is True
    assert r.consumerCare.phone is not None
    assert "1800 345 1720" in r.consumerCare.phone


def test_nandini_tollfree_phone_extracted():
    """'1800 425 8030' — standard 4+3+4 toll-free format."""
    r = _classify(NANDINI_LINES)
    assert r.consumerCare.found is True
    assert r.consumerCare.phone is not None
    assert "1800 425 8030" in r.consumerCare.phone


def test_haldirams_std_landline_phone_extracted():
    """'+91-120-2400286' is a +91-prefixed STD landline (area 120 = Noida,
    local 2400286). The old 5+5 pattern failed on this 3+7 grouping."""
    r = _classify(HALDIRAMS_LINES)
    assert r.consumerCare.found is True
    assert r.consumerCare.phone is not None
    assert "2400286" in r.consumerCare.phone, (
        f"Expected Noida landline in phone, got: {r.consumerCare.phone!r}"
    )


# --- Bug 3 tests: spaced PIN code stops address accumulation -----------------

def test_nandini_spaced_pin_stops_address_at_correct_line():
    """'Bengaluru - 560 029' contains the PIN in spaced 3+3 form. Without the
    fix, find_pin_code returned None, address accumulation continued, and the
    FSSAI licence number ('Lic. No. 10012043000053') was included in the
    manufacturer address string -- wrong and misleading."""
    r = _classify(NANDINI_LINES)
    assert r.manufacturer.found is True
    addr = r.manufacturer.address or ""
    assert "Lic. No." not in addr, (
        "FSSAI licence must not appear in manufacturer address -- "
        "spaced PIN '560 029' should have stopped accumulation"
    )


def test_nandini_manufacturer_name_correct():
    """Manufacturer name should be the federation, not 'KMF Nandini Dairy'
    (which is actually the manufacturing unit, not the party entity)."""
    r = _classify(NANDINI_LINES)
    assert r.manufacturer.found is True
    assert "Karnataka Co-operative" in r.manufacturer.name


def test_haldirams_manufacturer_address_free_of_ingredients():
    """Real failure mode: OCR merges two adjacent columns into ONE text line.
    The ingredients column (left) and manufacturer address column (right) sit
    at the same vertical position, so OCR emits a single block reading:

        'Gram Flour (Besan), Iodised Salt, Spices & Plot No. 145, Sector 63,'

    _is_same_column cannot help -- the text is already merged before we see it.
    _clean_address_line must strip the ingredient prefix and return only the
    address fragment starting at 'Plot No.'."""
    merged_lines = [
        _line("MANUFACTURED & PACKED BY: Haldiram Foods International Ltd.", 300, 280, 900, 300, 0.99),
        # This is the OCR-merged line -- ingredients on the left, address on the right
        _line("Gram Flour (Besan), Iodised Salt, Spices & Plot No. 145, Sector 63,", 300, 302, 900, 322, 0.97),
        _line("Noida - 201307, Uttar Pradesh, India", 550, 324, 900, 344, 0.96),
        _line("FOR CONSUMER COMPLAINTS / FEEDBACK:", 300, 400, 900, 420, 0.99),
        _line("call us at +91-120-2400286", 300, 422, 900, 442, 0.98),
        _line("NET WEIGHT   : 200 g", 50, 530, 900, 555, 0.99),
        _line("MRP Rs       : 60.00", 50, 558, 900, 580, 0.98),
    ]
    r = _classify(merged_lines)
    assert r.manufacturer.found is True
    addr = r.manufacturer.address or ""
    assert "Gram Flour" not in addr, (
        "Ingredient prefix leaked into address -- _clean_address_line didn't strip it"
    )
    assert "Spices" not in addr
    assert "Plot No. 145" in addr, f"Real address content missing, got: {addr!r}"
    # MRP must still be found on the structured info table below the block
    assert r.mrp.found is True, "MRP should be extracted from the label table"
    assert r.mrp.value == 60.0
    # Net quantity from the same table row
    assert r.netQuantity.found is True
    assert r.netQuantity.value == 200.0
    # Consumer care phone (STD landline +91-120-2400286) must be extracted
    assert r.consumerCare.found is True, "Consumer care section must be found"
    assert r.consumerCare.phone is not None, "STD landline must be in consumer care phone"
    assert "2400286" in r.consumerCare.phone

# --- Bug 4 tests: commodity classification -----------------------------------

def test_nandini_classified_as_dairy():
    """Nandini Toned Milk contains 'TONED MILK' and 'milk' -- must classify
    as Dairy. Before the fix there was no Dairy category at all, returning None."""
    r = _classify(NANDINI_LINES)
    assert r.commodity.found is True, "Dairy commodity must be found"
    assert r.commodity.category == "Dairy", (
        f"Expected 'Dairy', got {r.commodity.category!r}"
    )


def test_haldirams_classified_as_snacks():
    """Haldiram's Aloo Bhujia front panel says 'INDIAN SNACKS' (existing 'snack'
    keyword) AND 'ALOO BHUJIA' (new 'bhujia' keyword). Either alone is sufficient;
    having both gives higher confidence than any other competing category."""
    r = _classify(HALDIRAMS_LINES)
    assert r.commodity.found is True, "Snacks commodity must be found"
    assert r.commodity.category == "Snacks", (
        f"Expected 'Snacks', got {r.commodity.category!r}"
    )


def test_haldirams_savoury_treats_not_false_positive_for_other_category():
    """'SAVOURY TREATS' must not accidentally match a different category.
    Specifically, 'Salt' contains 'salt' in the ingredient list but that section
    is excluded from commodity classification. Confirms category isolation."""
    r = _classify(HALDIRAMS_LINES)
    assert r.commodity.category != "Salt"
    assert r.commodity.category != "Spices"


# --- Full-field sanity checks across all 5 products --------------------------

def test_bisleri_full_field_extraction():
    r = _classify(BISLERI_LINES)
    assert r.mrp.found and r.mrp.value == 20.0
    assert r.netQuantity.found and r.netQuantity.value == 1.0
    assert r.batchNumber.found and r.batchNumber.value == "B0724"
    assert r.packingDate.found and r.packingDate.month == 7 and r.packingDate.year == 2024
    assert r.expiryDate.found and r.expiryDate.month == 7 and r.expiryDate.year == 2025
    assert r.manufacturer.found and "Bisleri" in r.manufacturer.name
    assert r.commodity.found and r.commodity.category == "Packaged Drinking Water"


def test_dove_full_field_extraction():
    r = _classify(DOVE_LINES)
    assert r.mrp.found and r.mrp.value == 199.0
    assert r.netQuantity.found and r.netQuantity.value == 180.0
    assert r.batchNumber.found and r.batchNumber.value == "D0724"
    # Dove uses "Mfg. Date" (manufacturing), not "Date of Packaging" (packing)
    assert r.manufacturingDate.found and r.manufacturingDate.month == 7 and r.manufacturingDate.year == 2024
    assert r.expiryDate.found and r.expiryDate.year == 2025   # the key one
    assert r.manufacturer.found and "Unilever" in r.manufacturer.name
    assert r.commodity.found and r.commodity.category == "Cosmetic"


def test_tata_tea_full_field_extraction():
    r = _classify(TATA_TEA_LINES)
    assert r.mrp.found and r.mrp.value == 275.0
    assert r.netQuantity.found and r.netQuantity.value == 250.0
    assert r.batchNumber.found and r.batchNumber.value == "T0724"
    assert r.packingDate.found and r.packingDate.month == 7 and r.packingDate.year == 2024
    assert r.expiryDate.found and r.expiryDate.month == 7 and r.expiryDate.year == 2025
    assert r.manufacturer.found and "Tata" in r.manufacturer.name
    assert r.commodity.found and r.commodity.category == "Tea"


def test_nandini_full_field_extraction():
    r = _classify(NANDINI_LINES)
    assert r.mrp.found and r.mrp.value == 67.0
    assert r.netQuantity.found and r.netQuantity.value == 1.0
    assert r.batchNumber.found and r.batchNumber.value == "T0724"
    assert r.expiryDate.found and r.expiryDate.month == 1 and r.expiryDate.year == 2025


def test_haldirams_full_field_extraction():
    r = _classify(HALDIRAMS_LINES)
    assert r.mrp.found and r.mrp.value == 60.0
    assert r.netQuantity.found and r.netQuantity.value == 200.0
    assert r.batchNumber.found and r.batchNumber.value == "AB0724"
    assert r.packingDate.found and r.packingDate.month == 7 and r.packingDate.year == 2024
    assert r.expiryDate.found and r.expiryDate.month == 11 and r.expiryDate.year == 2024
    assert r.manufacturer.found and "Haldiram" in r.manufacturer.name
