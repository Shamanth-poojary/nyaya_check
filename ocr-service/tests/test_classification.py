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
