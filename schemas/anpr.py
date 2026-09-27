"""
Data contracts for Automatic Number Plate Recognition (ANPR) outputs.
Fulfills the required interface:
  plate text, plate confidence, vehicle/track association, and evidence reference where available.
Implements the crucial rule: "Do not assume OCR output is correct simply because text was returned."
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from .detection import BoundingBox


class PlateStandard(str, Enum):
    """Indian Motor Vehicles Act / MoRTH plate standards."""
    STANDARD_PRIVATE = "standard_private"  # White plate, black text (e.g., DL01AB1234)
    BHARAT_SERIES = "bharat_series"        # BH series (e.g., 22BH1234AA)
    COMMERCIAL = "commercial"              # Yellow plate, black text
    ELECTRIC_VEHICLE = "electric_vehicle"  # Green plate, white/yellow text
    DIPLOMATIC = "diplomatic"              # Blue plate, white text (e.g., 22CD12)
    MILITARY = "military"                  # Upward arrow prefix (e.g., ^01D123456)
    UNKNOWN_OR_CUSTOM = "unknown"


class PlateValidationStatus(str, Enum):
    """Integrity and validity status of plate recognition."""
    VALID = "valid"                        # Strictly conforms to recognized syntax & validation rules
    INVALID_SYNTAX = "invalid_syntax"      # Text found but fails format/character rules
    UNREADABLE = "unreadable"              # OCR could not extract discernible characters
    BLURRED = "blurred"                    # Rejected due to low Laplacian variance / motion blur
    LOW_CONTRAST = "low_contrast"          # Plate region lacks sufficient contrast for reliable binarization
    PARTIAL = "partial"                    # Incomplete plate (e.g. obscured/cropped)


class EvidenceReference(BaseModel):
    """
    Evidence record linking recognized number plate to physical/visual proof.
    Supports auditability, legal compliance, and human verification in security workflows.
    """
    evidence_id: str = Field(..., description="Unique evidence identifier (e.g. UUID)")
    camera_id: str = Field(..., description="Camera ID where evidence was captured")
    frame_sequence_number: int = Field(..., description="Frame index of capture")
    timestamp: datetime = Field(..., description="UTC capture timestamp")
    vehicle_track_id: Optional[int] = Field(default=None, description="Associated vehicle track ID")
    plate_bounding_box: BoundingBox = Field(..., description="Plate region bounding box in frame coordinates")
    vehicle_bounding_box: Optional[BoundingBox] = Field(
        default=None,
        description="Parent vehicle bounding box in frame coordinates"
    )
    image_uri: Optional[str] = Field(
        default=None,
        description="Storage path or URI to saved high-resolution evidence crop"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Audit attributes (e.g. image hash)")


class PlateRecord(BaseModel):
    """
    ANPR output record produced for a detected vehicle or plate region.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core interface fields required by Person 3 specification
    plate_text: Optional[str] = Field(
        default=None,
        description="Standardized, sanitized plate text (e.g. 'DL01AB1234'), or None if unreadable"
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Raw character string directly emitted by OCR engine before post-processing"
    )
    plate_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Synthesized confidence score combining OCR score, contrast, and syntax adherence"
    )
    vehicle_track_id: Optional[int] = Field(
        default=None,
        description="Associated vehicle track identifier (vehicle/track association)"
    )
    evidence_reference: Optional[EvidenceReference] = Field(
        default=None,
        description="Evidence pointer linking to visual proof and crop snapshot"
    )

    # Structural decomposition & validation metadata
    plate_bounding_box: Optional[BoundingBox] = Field(
        default=None,
        description="Plate location coordinates within the frame"
    )
    is_valid_format: bool = Field(
        default=False,
        description="Whether plate text strictly adheres to official MoRTH / BH format"
    )
    validation_status: PlateValidationStatus = Field(
        default=PlateValidationStatus.UNREADABLE,
        description="Diagnostic validation status"
    )
    standard: PlateStandard = Field(
        default=PlateStandard.UNKNOWN_OR_CUSTOM,
        description="Classification of plate standard"
    )
    state_code: Optional[str] = Field(default=None, description="2-letter Indian state/UT code (e.g. DL, MH, KA)")
    district_code: Optional[str] = Field(default=None, description="2-digit district/RTO code (e.g. 01, 12)")
    series: Optional[str] = Field(default=None, description="1-3 letter series code (e.g. AB, CD)")
    registration_number: Optional[str] = Field(default=None, description="4-digit registration number (e.g. 1234)")

    limitations: List[str] = Field(
        default_factory=list,
        description="Explicit documentation of why plate was rejected, degraded, or low confidence"
    )
    frame_sequence_number: Optional[int] = Field(default=None, description="Frame index of observation")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Observation timestamp"
    )

    @property
    def is_readable(self) -> bool:
        return self.plate_text is not None and len(self.plate_text) >= 4 and self.validation_status == PlateValidationStatus.VALID
