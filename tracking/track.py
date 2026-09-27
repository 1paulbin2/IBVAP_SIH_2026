"""
Single track state machine, Kalman lifecycle, and trajectory history manager.
Maintains object identity, handles temporary occlusion, and records trajectory for analytics.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from schemas.detection import BoundingBox, DetectionRecord
from schemas.tracking import TrackedObject, TrackState, TrajectoryPoint
from .kalman_filter import KalmanBoxTracker


class SingleTrack:
    """
    Stateful representation of a tracked object over time.
    """

    def __init__(
        self,
        track_id: int,
        detection: DetectionRecord,
        frame_sequence_number: int,
        min_hits: int = 2,
        max_age: int = 30,
        max_trajectory_length: int = 300,
    ):
        self.track_id = track_id
        self.object_class = detection.class_name
        self.confidence = float(detection.confidence)
        self.min_hits = min_hits
        self.max_age = max_age
        self.max_trajectory_length = max_trajectory_length

        # State lifecycle
        # If min_hits <= 1, immediately start as CONFIRMED, else TENTATIVE
        self.state: TrackState = TrackState.CONFIRMED if min_hits <= 1 else TrackState.TENTATIVE
        self.age: int = 1
        self.hits: int = 1
        self.time_since_update: int = 0

        # Initialize Kalman Filter
        init_xyxy = detection.bounding_box.to_xyxy()
        self.kalman = KalmanBoxTracker(init_xyxy)

        # Trajectory history
        self.trajectory: List[TrajectoryPoint] = []
        self._record_trajectory_point(
            frame_sequence_number=frame_sequence_number,
            timestamp=detection.timestamp,
            bbox=detection.bounding_box,
            vx=0.0,
            vy=0.0,
        )

        # ANPR association cache
        self.associated_plate_text: Optional[str] = None
        self.associated_plate_confidence: Optional[float] = None
        self.plate_observations: List[Tuple[str, float]] = []

    def _record_trajectory_point(
        self,
        frame_sequence_number: int,
        timestamp: datetime,
        bbox: BoundingBox,
        vx: Optional[float] = None,
        vy: Optional[float] = None,
    ) -> None:
        cx, cy = bbox.center
        point = TrajectoryPoint(
            frame_sequence_number=frame_sequence_number,
            timestamp=timestamp,
            center_x=cx,
            center_y=cy,
            bounding_box=bbox,
            velocity_x=vx,
            velocity_y=vy,
        )
        self.trajectory.append(point)
        if len(self.trajectory) > self.max_trajectory_length:
            self.trajectory.pop(0)

    @property
    def current_bounding_box(self) -> BoundingBox:
        """Current estimated bounding box from Kalman filter."""
        x1, y1, x2, y2 = self.kalman.current_xyxy
        return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)

    def predict(self) -> BoundingBox:
        """
        Predict next bounding box using Kalman motion model.
        Advances Kalman state and increments age.
        """
        pred_xyxy = self.kalman.predict()
        self.age += 1
        return BoundingBox(x1=pred_xyxy[0], y1=pred_xyxy[1], x2=pred_xyxy[2], y2=pred_xyxy[3])

    def update(
        self,
        detection: DetectionRecord,
        frame_sequence_number: int,
    ) -> None:
        """
        Update track with an observed detection in the current frame.
        """
        # Kalman update
        obs_xyxy = detection.bounding_box.to_xyxy()
        self.kalman.update(obs_xyxy)

        self.hits += 1
        self.time_since_update = 0

        # Update class and exponential moving average confidence
        self.object_class = detection.class_name
        self.confidence = 0.7 * self.confidence + 0.3 * float(detection.confidence)

        # Transition tentative to confirmed once min_hits reached
        if self.state == TrackState.TENTATIVE and self.hits >= self.min_hits:
            self.state = TrackState.CONFIRMED
        elif self.state == TrackState.LOST:
            self.state = TrackState.CONFIRMED

        # Record trajectory
        vx, vy = self.kalman.velocity
        curr_box = self.current_bounding_box
        self._record_trajectory_point(
            frame_sequence_number=frame_sequence_number,
            timestamp=detection.timestamp,
            bbox=curr_box,
            vx=vx,
            vy=vy,
        )

    def mark_missed(
        self,
        frame_sequence_number: int,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Record a frame where this track was not matched with an observation.
        Maintains continuity during temporary occlusion/missed detections.
        """
        self.time_since_update += 1

        if self.state == TrackState.CONFIRMED:
            self.state = TrackState.LOST

        if self.time_since_update > self.max_age:
            self.state = TrackState.REMOVED
        else:
            # During temporary occlusion, record the Kalman-predicted position in trajectory
            ts = timestamp or datetime.now(timezone.utc)
            vx, vy = self.kalman.velocity
            self._record_trajectory_point(
                frame_sequence_number=frame_sequence_number,
                timestamp=ts,
                bbox=self.current_bounding_box,
                vx=vx,
                vy=vy,
            )

    def add_plate_observation(self, plate_text: str, confidence: float) -> None:
        """Add a plate observation to temporal voting cache."""
        self.plate_observations.append((plate_text, confidence))
        # Keep highest confidence observation or most frequent
        best_obs = max(self.plate_observations, key=lambda x: x[1])
        self.associated_plate_text = best_obs[0]
        self.associated_plate_confidence = best_obs[1]

    def to_schema(self, timestamp: Optional[datetime] = None) -> TrackedObject:
        """Convert to external Pydantic TrackedObject schema."""
        ts = timestamp or (self.trajectory[-1].timestamp if self.trajectory else datetime.now(timezone.utc))
        vx, vy = self.kalman.velocity
        return TrackedObject(
            track_id=self.track_id,
            object_class=self.object_class,
            bounding_box=self.current_bounding_box,
            timestamp=ts,
            confidence=round(self.confidence, 4),
            state=self.state,
            age=self.age,
            hits=self.hits,
            time_since_update=self.time_since_update,
            trajectory=list(self.trajectory),
            velocity=(round(vx, 2), round(vy, 2)),
            associated_plate_text=self.associated_plate_text,
            associated_plate_confidence=round(self.associated_plate_confidence, 4) if self.associated_plate_confidence else None,
        )
