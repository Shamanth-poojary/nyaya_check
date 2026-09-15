"""
Draft response schema for the /extract endpoint.

This mirrors the "Target Compliance-Ready JSON" described in the project
context doc (section 24). It is intentionally a DRAFT: the real contract
should be frozen with the rest of the team once fields stabilize (Phase 10).

Every mandatory field carries `found` + `confidence` so the rules engine can
tell "not present on package" apart from "not extracted yet / low confidence".
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    xmin: int
    ymin: int
    xmax: int
    ymax: int


class RawOCRLine(BaseModel):
    text: str
    bbox: BoundingBox
    confidence: float
    sourceImage: Optional[str] = None


class Commodity(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    found: bool = False
    confidence: float = 0.0
    sourceImage: Optional[str] = None  # which uploaded photo this evidence came from


class PartyInfo(BaseModel):
    """Shared shape for Manufacturer / Packer / Importer."""
    name: Optional[str] = None
    address: Optional[str] = None
    role: Optional[str] = None
    found: bool = False
    confidence: float = 0.0
    sourceImage: Optional[str] = None  # which uploaded photo this evidence came from


class MRP(BaseModel):
    value: Optional[float] = None
    currency: str = "INR"
    taxIncluded: Optional[bool] = None
    raw: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0
    sourceImage: Optional[str] = None  # which uploaded photo this evidence came from


class NetQuantity(BaseModel):
    rawValue: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    quantityType: Optional[str] = None
    normalizedValue: Optional[float] = None
    normalizedUnit: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0
    sourceImage: Optional[str] = None  # which uploaded photo this evidence came from


class DateField(BaseModel):
    """Shared shape for manufacturing / expiry / packing dates."""
    raw: Optional[str] = None
    dateType: Optional[str] = None  # manufacturing | expiry | packing | import
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0
    sourceImage: Optional[str] = None  # which uploaded photo this evidence came from


class BatchNumber(BaseModel):
    """Not in the original contract -- added after real test photos showed
    a 'B.NO:...' batch/lot code that has nowhere else to go."""
    value: Optional[str] = None
    raw: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0
    sourceImage: Optional[str] = None  # which uploaded photo this evidence came from


class Dimension(BaseModel):
    label: Optional[str] = None  # e.g. "length", "width"
    value: Optional[float] = None
    unit: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    sourceImage: Optional[str] = None


class ConsumerCare(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0
    sourceImage: Optional[str] = None  # which uploaded photo this evidence came from


class QuantityQualifier(BaseModel):
    text: str
    qualifierType: str  # WHEN_PACKED | MINIMUM | NOT_LESS_THAN | AVERAGE | ...
    bbox: Optional[BoundingBox] = None
    sourceImage: Optional[str] = None


class MisleadingTerm(BaseModel):
    text: str  # e.g. "approximately", "about", "dozen"
    bbox: Optional[BoundingBox] = None
    sourceImage: Optional[str] = None


class Measurement(BaseModel):
    """Physical measurement, kept separate from the declared label value.
    Never inferred from a photo -- only populated if supplied externally."""
    available: bool = False
    actualValue: Optional[float] = None
    actualUnit: Optional[str] = None


# ---------------------------------------------------------------------------
# Phase 02 Visual Analysis models
# All values are RELATIVE or QUALITATIVE.  No absolute physical measurements
# (mm, point sizes) are ever produced here -- only pixel-space ratios derived
# from the same uncalibrated photo's coordinate system, labeled as such.
# ---------------------------------------------------------------------------

class FontSizeEntry(BaseModel):
    """Relative font-size evidence for one classified field.

    heightPx is the bbox height in the *original* photo's pixel coordinate
    system (already inverse-scaled back from any internal resizing).
    ratioToNetQuantity is heightPx / netQuantity.heightPx; None when
    netQuantity has no bbox.  These are pixel ratios, not physical sizes.
    """
    field: str                              # classifier field name, e.g. "mrp", "netQuantity"
    heightPx: int                           # bbox height in original-photo pixels (relative, not physical)
    ratioToNetQuantity: Optional[float] = None  # None if netQuantity bbox unavailable


class ContrastEntry(BaseModel):
    """Contrast measurement for one classified field's bbox region.

    stdDev is the grayscale pixel-intensity standard deviation within the
    cropped bbox region -- a RELATIVE indicator of visual contrast, not a
    photometric calibrated measurement.  bucket maps it to a qualitative label.
    """
    field: str
    stdDev: float   # grayscale std-dev of pixel intensities within crop (relative)
    bucket: str     # "low" | "medium" | "high"  (thresholds: <20, 20-50, >=50)


class ReadabilityEntry(BaseModel):
    """Qualitative readability flag for one classified field.

    Combination heuristic (documented in app/visual/contrast.py):
      hard_to_read if contrast.bucket == "low"
                   OR (contrast.bucket == "medium" AND ratioToNetQuantity < 0.5)
      readable otherwise.
    This is a HEURISTIC SIGNAL, not a certified measurement.  The Phase 03
    rules engine should treat "hard_to_read" as a soft signal, not a hard fail.
    """
    field: str
    readability: str    # "readable" | "hard_to_read"
    reason: str         # e.g. "low_contrast", "small_relative_size", "ok"


class QuantityClearance(BaseModel):
    """Whitespace clearance around the net quantity declaration.

    Each ratio = distance-to-nearest-neighbor-in-pixels / netQuantity-bbox-height.
    Neighbor = nearest other rawOCR bbox in that cardinal direction, or the
    image edge if no text is closer.  These are pixel ratios in the original
    photo's coordinate space; they do NOT represent physical mm clearances.
    None means the net quantity field has no bbox and clearance cannot be computed.
    """
    aboveRatio: Optional[float] = None
    belowRatio: Optional[float] = None
    leftRatio: Optional[float] = None
    rightRatio: Optional[float] = None
    note: str = ""      # human-readable explanation / caveat


class PrincipalDisplayPanel(BaseModel):
    """Heuristic identification of the Principal Display Panel image.

    For multi-image submissions: the sourceImage that contributed the most of
    {commodity, netQuantity, mrp} is identified as the likely PDP.
    For single-image submissions: trivially identified as the only image.
    isHeuristic is always True -- this is an inference from field-source tags,
    not from photo metadata (there is none).
    """
    likelySourceImage: Optional[str] = None    # filename of likely PDP; None if undetermined
    isHeuristic: bool = True
    note: str = ""      # explanation, e.g. "single-image submission" or "2 of 3 PDP fields sourced here"


class VisualEvidence(BaseModel):
    """Phase 02 visual analysis results.

    All fields are relative/qualitative indicators derived from pixel data.
    No absolute physical measurements are present.  See individual model
    docstrings for the exact meaning of each metric.
    """
    relativeFontSizes: List[FontSizeEntry] = Field(default_factory=list)
    # Ratio of netQuantity bbox height to median rawOCR line height on same photo.
    # None when netQuantity has no bbox or rawOCR is empty.
    netQuantityMedianRatio: Optional[float] = None
    contrast: List[ContrastEntry] = Field(default_factory=list)
    readability: List[ReadabilityEntry] = Field(default_factory=list)
    quantityClearance: Optional[QuantityClearance] = None
    principalDisplayPanel: Optional[PrincipalDisplayPanel] = None


class DocumentMeta(BaseModel):
    imageId: str
    width: int
    height: int


SCHEMA_VERSION: str = "2.0"


class ExtractionResponse(BaseModel):
    schemaVersion: str = SCHEMA_VERSION
    document: DocumentMeta
    sourceDocuments: List[DocumentMeta] = Field(default_factory=list)  # populated for multi-image extraction
    commodity: Commodity = Field(default_factory=Commodity)
    manufacturer: PartyInfo = Field(default_factory=PartyInfo)
    packer: PartyInfo = Field(default_factory=PartyInfo)
    importer: PartyInfo = Field(default_factory=PartyInfo)
    mrp: MRP = Field(default_factory=MRP)
    netQuantity: NetQuantity = Field(default_factory=NetQuantity)
    manufacturingDate: DateField = Field(default_factory=DateField)
    packingDate: DateField = Field(default_factory=DateField)  # "Date of Packaging" -- distinct from mfg date, very common on real labels
    expiryDate: DateField = Field(default_factory=DateField)
    batchNumber: BatchNumber = Field(default_factory=BatchNumber)
    dimensions: List[Dimension] = Field(default_factory=list)
    consumerCare: ConsumerCare = Field(default_factory=ConsumerCare)
    quantityQualifiers: List[QuantityQualifier] = Field(default_factory=list)
    misleadingQuantityTerms: List[MisleadingTerm] = Field(default_factory=list)
    measurement: Measurement = Field(default_factory=Measurement)
    visual: VisualEvidence = Field(default_factory=VisualEvidence)
    rawOCR: List[RawOCRLine] = Field(default_factory=list)
    uncertainFields: List[str] = Field(default_factory=list)


def empty_response(image_id: str, width: int, height: int) -> ExtractionResponse:
    """Phase-1 placeholder: valid shape, nothing extracted yet."""
    return ExtractionResponse(
        document=DocumentMeta(imageId=image_id, width=width, height=height)
    )
