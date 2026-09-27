"""
Data contracts for tracking outputs produced by Person 3 (Tracking Module).
Matches the required interface: track_id, object_class, bounding_box, timestamp, confidence,
and provides trajectory history needed by downstream event analytics (Person 4).
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from .detection import BoundingBox


class TrackState(str, Enum):
    """Lifecycle state of a tracked object."""
    TENTATIVE = "tentative"    # Newly detected object, not yet confirmed over min_hits frames
    CONFIRMED = "confirmed"    # Actively tracked object with stable identity
    LOST = "lost"              # Missed in recent frames, position estimated via Kalman prediction
    REMOVED = "removed"        # Deleted after max_age frames without re-detection


class TrajectoryPoint(BaseModel):
    """
    Spatial-temporal trajectory point along an object's path.
    Essential for Person 4's event analytics (speed estimation, wrong-way detection, dwell time, line-crossing).
    """
    frame_sequence_number: int = Field(..., description="Frame index when point was recorded")
    timestamp: datetime = Field(..., description="UTC timestamp of the point")
    center_x: float = Field(..., description="Centroid X in pixels")
    center_y: float = Field(..., description="Centroid Y in pixels")
    bounding_box: BoundingBox = Field(..., description="Bounding box at this point")
    velocity_x: Optional[float] = Field(default=None, description="Estimated X velocity (pixels/frame or pixels/sec)")
    velocity_y: Optional[float] = Field(default=None, description="Estimated Y velocity (pixels/frame or pixels/sec)")

    @property
    def point(self) -> Tuple[float, float]:
        return (self.center_x, self.center_y)


class TrackedObject(BaseModel):
    """
    Standard Tracking output record emitted by Person 3.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    track_id: int = Field(..., description="Persistent, stable unique object identifier")
    object_class: str = Field(..., description="Object classification (e.g. car, truck, bus, motorcycle)")
    bounding_box: BoundingBox = Field(..., description="Current smoothed/predicted bounding box")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the track observation"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Smoothed or latest detection confidence score")

    # Additional rich tracking metadata for analytics
    state: TrackState = Field(default=TrackState.CONFIRMED, description="Current track lifecycle state")
    age: int = Field(default=1, description="Total frames since track was initialized")
    hits: int = Field(default=1, description="Total frames where track was successfully matched with a detection")
    time_since_update: int = Field(default=0, description="Frames elapsed since last actual detection match")
    trajectory: List[TrajectoryPoint] = Field(
        default_factory=list,
        description="Chronological spatial-temporal trajectory history"
    )
    velocity: Optional[Tuple[float, float]] = Field(
        default=None,
        description="Estimated velocity vector (vx, vy)"
    )
    associated_plate_text: Optional[str] = Field(
        default=None,
        description="License plate text associated with this vehicle track (if recognized)"
    )
    associated_plate_confidence: Optional[float] = Field(
        default=None,
        description="Confidence of the associated license plate"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom tracker properties")

    @property
    def is_confirmed(self) -> bool:
        return self.state == TrackState.CONFIRMED

    @property
    def is_lost(self) -> bool:
        return self.state == TrackState.LOST

    @property
    def centroid(self) -> Tuple[float, float]:
        return self.bounding_box.center

    @property
    def trajectory_length(self) -> int:
        return len(self.trajectory)

    def total_distance_traveled(self) -> float:
        """Calculate cumulative Euclidean distance traveled across trajectory points in pixels."""
        if len(self.trajectory) < 2:
            return 0.0
        dist = 0.0
        for i in range(1, len(self.trajectory)):
            p1 = self.trajectory[i - 1]
            p2 = self.trajectory[i]
            dx = p2.center_x - p1.center_x
            dy = p2.center_y - p1.center_y
            dist += (dx * dx + dy * dy) ** 0.5
        return dist


class TrackingBatch(BaseModel):
    """
    Output batch of active tracks for a single processed frame.
    """
    camera_id: str = Field(..., description="Camera ID")
    frame_sequence_number: int = Field(..., description="Frame sequence index")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Frame timestamp"
    )
    active_tracks: List[TrackedObject] = Field(
        default_factory=list,
        description="List of all currently active/confirmed tracks"
    )
    lost_tracks: List[TrackedObject] = Field(
        default_factory=list,
        description="Tracks temporarily unobserved in this frame but retained in memory"
    )
