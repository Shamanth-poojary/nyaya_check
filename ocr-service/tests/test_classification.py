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

# Captured from hana3.jpeg (back label: manufacturer, consumer care, etc.)
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
