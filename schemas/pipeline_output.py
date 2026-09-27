"""
Unified output schema uniting Person 3's Tracking and ANPR results for downstream consumption.
Person 4 (Event Analytics / Rules Engine) consumes this data contract.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from .tracking import TrackedObject
from .anpr import PlateRecord


class PipelineFrameResult(BaseModel):
    """
    Combined output for a single video frame containing:
    - active vehicle tracks with motion trajectories
    - associated number plates recognized in this frame
    - execution metrics (tracker latency, ANPR latency)
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    camera_id: str = Field(..., description="Camera ID")
    frame_sequence_number: int = Field(..., description="Processed frame sequence number")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Frame timestamp"
    )
    tracked_objects: List[TrackedObject] = Field(
        default_factory=list,
        description="All confirmed and active vehicle tracks in this frame"
    )
    plate_records: List[PlateRecord] = Field(
        default_factory=list,
        description="All ANPR plate records recognized/evaluated in this frame"
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Processing latency metrics (e.g. tracking_ms, anpr_ms, total_ms)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supplemental pipeline telemetry"
    )

    def get_track(self, track_id: int) -> Optional[TrackedObject]:
        """Find tracked object by track_id."""
        for t in self.tracked_objects:
            if t.track_id == track_id:
                return t
        return None

    def get_plate_for_track(self, track_id: int) -> Optional[PlateRecord]:
        """Find plate record associated with a track_id."""
        for p in self.plate_records:
            if p.vehicle_track_id == track_id:
                return p
        return None
