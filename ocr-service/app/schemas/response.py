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


class Commodity(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    found: bool = False
    confidence: float = 0.0


class PartyInfo(BaseModel):
    """Shared shape for Manufacturer / Packer / Importer."""
    name: Optional[str] = None
    address: Optional[str] = None
    role: Optional[str] = None
    found: bool = False
    confidence: float = 0.0


class MRP(BaseModel):
    value: Optional[float] = None
    currency: str = "INR"
    taxIncluded: Optional[bool] = None
    raw: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0


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


class ManufacturingDate(BaseModel):
    raw: Optional[str] = None
    dateType: Optional[str] = None  # manufacturing | packing | import
    month: Optional[int] = None
    year: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0


class Dimension(BaseModel):
    label: Optional[str] = None  # e.g. "length", "width"
    value: Optional[float] = None
    unit: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class ConsumerCare(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    found: bool = False
    confidence: float = 0.0


class QuantityQualifier(BaseModel):
    text: str
    qualifierType: str  # WHEN_PACKED | MINIMUM | NOT_LESS_THAN | AVERAGE | ...
    bbox: Optional[BoundingBox] = None


class MisleadingTerm(BaseModel):
    text: str  # e.g. "approximately", "about", "dozen"
    bbox: Optional[BoundingBox] = None


class Measurement(BaseModel):
    """Physical measurement, kept separate from the declared label value.
    Never inferred from a photo -- only populated if supplied externally."""
    available: bool = False
    actualValue: Optional[float] = None
    actualUnit: Optional[str] = None


class VisualEvidence(BaseModel):
    textRegions: List[dict] = Field(default_factory=list)
    relativeFontSizes: dict = Field(default_factory=dict)
    contrast: dict = Field(default_factory=dict)
    readability: dict = Field(default_factory=dict)
    quantityClearance: dict = Field(default_factory=dict)
    principalDisplayPanel: dict = Field(default_factory=dict)


class DocumentMeta(BaseModel):
    imageId: str
    width: int
    height: int


class ExtractionResponse(BaseModel):
    document: DocumentMeta
    commodity: Commodity = Field(default_factory=Commodity)
    manufacturer: PartyInfo = Field(default_factory=PartyInfo)
    packer: PartyInfo = Field(default_factory=PartyInfo)
    importer: PartyInfo = Field(default_factory=PartyInfo)
    mrp: MRP = Field(default_factory=MRP)
    netQuantity: NetQuantity = Field(default_factory=NetQuantity)
    manufacturingDate: ManufacturingDate = Field(default_factory=ManufacturingDate)
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
