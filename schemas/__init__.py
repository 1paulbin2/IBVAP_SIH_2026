"""
Schemas package export for Person 3 (Tracking + ANPR).
"""

from .detection import BoundingBox, DetectionRecord, FrameDetections
from .tracking import TrackedObject, TrackState, TrajectoryPoint, TrackingBatch
from .anpr import PlateRecord, PlateStandard, PlateValidationStatus, EvidenceReference
from .pipeline_output import PipelineFrameResult

__all__ = [
    "BoundingBox",
    "DetectionRecord",
    "FrameDetections",
    "TrackedObject",
    "TrackState",
    "TrajectoryPoint",
    "TrackingBatch",
    "PlateRecord",
    "PlateStandard",
    "PlateValidationStatus",
    "EvidenceReference",
    "PipelineFrameResult",
]
