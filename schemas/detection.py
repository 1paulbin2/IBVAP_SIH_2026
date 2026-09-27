"""
Data contracts for object detections produced by Person 2 (Object Detection Module).
Person 3 (Tracking + ANPR) consumes these detection records or mock detections.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BoundingBox(BaseModel):
    """
    Standard bounding box represented as [x1, y1, x2, y2]
    where (x1, y1) is top-left and (x2, y2) is bottom-right in pixel coordinates.
    """
    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")

    @field_validator("x2")
    @classmethod
    def validate_width(cls, v: float, info) -> float:
        x1 = info.data.get("x1")
        if x1 is not None and v <= x1:
            raise ValueError(f"x2 ({v}) must be greater than x1 ({x1})")
        return v

    @field_validator("y2")
    @classmethod
    def validate_height(cls, v: float, info) -> float:
        y1 = info.data.get("y1")
        if y1 is not None and v <= y1:
            raise ValueError(f"y2 ({v}) must be greater than y1 ({y1})")
        return v

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        """Width / Height"""
        return self.width / max(self.height, 1e-6)

    @property
    def center(self) -> Tuple[float, float]:
        """(center_x, center_y)"""
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def to_xyxy(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    def to_xywh(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.width, self.height)

    def to_int_xyxy(self) -> Tuple[int, int, int, int]:
        return (int(round(self.x1)), int(round(self.y1)), int(round(self.x2)), int(round(self.y2)))

    def crop_from(self, image: np.ndarray) -> np.ndarray:
        """Safely crop this bounding box from an image array."""
        h, w = image.shape[:2]
        x1 = max(0, min(int(round(self.x1)), w - 1))
        y1 = max(0, min(int(round(self.y1)), h - 1))
        x2 = max(x1 + 1, min(int(round(self.x2)), w))
        y2 = max(y1 + 1, min(int(round(self.y2)), h))
        return image[y1:y2, x1:x2].copy()

    def iou(self, other: BoundingBox) -> float:
        """Calculate Intersection over Union (IoU) with another bounding box."""
        ix1 = max(self.x1, other.x1)
        iy1 = max(self.y1, other.y1)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)

        iw = max(0.0, ix2 - ix1)
        ih = max(0.0, iy2 - iy1)
        intersection = iw * ih

        union = self.area + other.area - intersection
        if union <= 0.0:
            return 0.0
        return intersection / union

    def contains(self, other: BoundingBox, tolerance: float = 0.0) -> bool:
        """Check whether other bounding box is contained inside this box (e.g., plate inside vehicle)."""
        return (
            other.x1 >= (self.x1 - tolerance)
            and other.y1 >= (self.y1 - tolerance)
            and other.x2 <= (self.x2 + tolerance)
            and other.y2 <= (self.y2 + tolerance)
        )


class DetectionRecord(BaseModel):
    """
    Standard single detection record produced by Person 2's detector (or mock generator).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    detection_id: str = Field(..., description="Unique ID for detection event")
    camera_id: str = Field(default="default_cam", description="Origin camera identifier")
    frame_sequence_number: Optional[int] = Field(default=None, description="Sequence index of the frame")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of capture"
    )
    class_name: str = Field(..., description="Detected class (e.g. car, truck, bus, motorcycle, license_plate)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score [0.0 - 1.0]")
    bounding_box: BoundingBox = Field(..., description="Object bounding box [x1, y1, x2, y2]")
    plate_bounding_box: Optional[BoundingBox] = Field(
        default=None,
        description="Optional license plate bbox if detected simultaneously by Person 2"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Supplemental detector attributes")


class FrameDetections(BaseModel):
    """
    Collection of detections for a single video frame.
    Serves as the input batch to Person 3 (Tracker + ANPR).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    camera_id: str = Field(..., description="Camera ID")
    frame_sequence_number: int = Field(..., ge=0, description="Frame sequence index")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp"
    )
    detections: List[DetectionRecord] = Field(
        default_factory=list,
        description="List of vehicle and object detections in this frame"
    )
    frame: Optional[np.ndarray] = Field(
        default=None,
        description="Optional full image ndarray (BGR) for plate cropping and OCR"
    )

    @property
    def vehicle_detections(self) -> List[DetectionRecord]:
        """Return detections belonging to vehicle classes."""
        vehicle_classes = {"car", "truck", "bus", "motorcycle", "van", "auto", "vehicle"}
        return [d for d in self.detections if d.class_name.lower() in vehicle_classes]

    @property
    def plate_detections(self) -> List[DetectionRecord]:
        """Return detections specifically classified as license plates."""
        plate_classes = {"license_plate", "plate", "number_plate", "registration_plate"}
        return [d for d in self.detections if d.class_name.lower() in plate_classes]
