from dataclasses import dataclass
from typing import Optional

@dataclass
class BoundingBox:
    """
    Bounding box representation using [x_min, y_min, x_max, y_max] format.
    x_min, y_min: Top-left coordinate
    x_max, y_max: Bottom-right coordinate
    
    Coordinates are absolute pixel values (integers).
    """
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    
    def __post_init__(self):
        if self.x_max < self.x_min or self.y_max < self.y_min:
            raise ValueError(f"Invalid bounding box coordinates: {self}")

@dataclass
class DetectionResult:
    """
    Structured output for a single object detection.
    This structure is designed to be cleanly consumed by the Tracking/ANPR module.
    """
    class_name: str
    class_id: int
    confidence: float
    bbox: BoundingBox
    timestamp: Optional[float] = None
    camera_id: Optional[str] = None
    
    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence score must be between 0.0 and 1.0. Got: {self.confidence}")
