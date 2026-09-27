"""
Abstract base class for multi-object trackers in Person 3.
Ensures pluggability and standardized interface across tracking implementations.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from schemas.detection import FrameDetections, DetectionRecord
from schemas.tracking import TrackedObject, TrackingBatch


class BaseTracker(ABC):
    """
    Abstract tracker interface.
    Consumes Person 2's FrameDetections and produces stable TrackedObject records.
    """

    @abstractmethod
    def update(self, frame_detections: FrameDetections) -> List[TrackedObject]:
        """
        Process a new frame's detections and return the list of active tracked objects.

        Args:
            frame_detections: Detections in the current frame, including bounding boxes,
                              confidences, frame timestamp and sequence number.

        Returns:
            List of TrackedObject instances with consistent track_id and updated trajectory.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal tracker state and ID counter."""
        pass
