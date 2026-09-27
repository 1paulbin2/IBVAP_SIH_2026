"""
ByteTrack Multi-Object Tracking implementation for Person 3.
Provides stable object IDs across frames, two-stage detection association,
and robust handling of temporary missed detections and occlusions.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np

from schemas.detection import DetectionRecord, FrameDetections
from schemas.tracking import TrackedObject, TrackState
from .base import BaseTracker
from .matching import calculate_iou_matrix, linear_assignment
from .track import SingleTrack


class ByteTracker(BaseTracker):
    """
    ByteTrack implementation for robust vehicle tracking in surveillance feeds.
    Features:
    - Two-stage association (first high-score detections, then low-score detections for occlusion recovery)
    - Kalman filter motion prediction
    - Trajectory recording for Person 4 analytics
    - Preserves stable IDs across temporary missed detections for up to max_age frames
    """

    def __init__(
        self,
        track_thresh: float = 0.5,
        match_thresh: float = 0.3,
        match_thresh_low: float = 0.1,
        min_hits: int = 2,
        max_age: int = 30,
        return_lost: bool = False,
    ):
        """
        Args:
            track_thresh: Detection confidence threshold to consider in primary matching.
            match_thresh: Minimum IoU required for matching in first stage (cost = 1.0 - IoU <= 1.0 - match_thresh).
            match_thresh_low: Minimum IoU required for matching in second stage (low-confidence recovery).
            min_hits: Number of consecutive detections required to confirm a track.
            max_age: Maximum frames to retain a track without detection updates before removal.
            return_lost: Whether to include temporarily lost tracks (Kalman-predicted) in returned output.
        """
        self.track_thresh = track_thresh
        self.match_cost_thresh = 1.0 - match_thresh
        self.match_cost_thresh_low = 1.0 - match_thresh_low
        self.min_hits = min_hits
        self.max_age = max_age
        self.return_lost = return_lost

        self._next_id: int = 1
        self.tracked_tracks: List[SingleTrack] = []  # Confirmed tracks
        self.lost_tracks: List[SingleTrack] = []     # Temporarily lost tracks
        self.tentative_tracks: List[SingleTrack] = []# Unconfirmed tracks

    def reset(self) -> None:
        """Reset all active tracks and reset ID counter."""
        self._next_id = 1
        self.tracked_tracks.clear()
        self.lost_tracks.clear()
        self.tentative_tracks.clear()

    def _get_next_id(self) -> int:
        tid = self._next_id
        self._next_id += 1
        return tid

    def update(self, frame_detections: FrameDetections) -> List[TrackedObject]:
        """
        Process incoming frame detections and return active tracked objects.
        """
        frame_seq = frame_detections.frame_sequence_number
        timestamp = frame_detections.timestamp
        raw_detections = frame_detections.vehicle_detections

        # 1. Advance all tracks with Kalman prediction
        all_pool = self.tracked_tracks + self.lost_tracks
        for track in all_pool:
            track.predict()
        for track in self.tentative_tracks:
            track.predict()

        # 2. Partition detections into high and low confidence groups
        high_dets: List[DetectionRecord] = []
        low_dets: List[DetectionRecord] = []

        for d in raw_detections:
            if d.confidence >= self.track_thresh:
                high_dets.append(d)
            elif d.confidence >= 0.1:  # Floor threshold to reject complete noise
                low_dets.append(d)

        # -------------------------------------------------------------
        # Step 3: First Association (High-score detections vs Confirmed/Lost)
        # -------------------------------------------------------------
        track_candidates = [t for t in all_pool]
        matches_a, unmatched_tracks_a, unmatched_dets_a = self._match(
            tracks=track_candidates,
            detections=high_dets,
            max_cost=self.match_cost_thresh
        )

        for t_idx, d_idx in matches_a:
            track = track_candidates[t_idx]
            det = high_dets[d_idx]
            track.update(det, frame_sequence_number=frame_seq)

        # -------------------------------------------------------------
        # Step 4: Second Association (Low-score detections vs Unmatched Confirmed/Lost)
        # Recovers temporarily occluded vehicles and motion-blurred targets
        # -------------------------------------------------------------
        unmatched_pool_tracks = [track_candidates[i] for i in unmatched_tracks_a]
        matches_b, unmatched_tracks_b, _ = self._match(
            tracks=unmatched_pool_tracks,
            detections=low_dets,
            max_cost=self.match_cost_thresh_low
        )

        for t_idx, d_idx in matches_b:
            track = unmatched_pool_tracks[t_idx]
            det = low_dets[d_idx]
            track.update(det, frame_sequence_number=frame_seq)

        # Tracks still unmatched after stage 2 are marked as missed
        final_unmatched_tracks = [unmatched_pool_tracks[i] for i in unmatched_tracks_b]
        for track in final_unmatched_tracks:
            track.mark_missed(frame_sequence_number=frame_seq, timestamp=timestamp)

        # -------------------------------------------------------------
        # Step 5: Third Association (Remaining High-score detections vs Tentative tracks)
        # -------------------------------------------------------------
        remaining_high_dets = [high_dets[i] for i in unmatched_dets_a]
        matches_c, unmatched_tentative, unmatched_high_dets = self._match(
            tracks=self.tentative_tracks,
            detections=remaining_high_dets,
            max_cost=self.match_cost_thresh
        )

        for t_idx, d_idx in matches_c:
            track = self.tentative_tracks[t_idx]
            det = remaining_high_dets[d_idx]
            track.update(det, frame_sequence_number=frame_seq)

        # Unmatched tentative tracks are marked as missed
        for idx in unmatched_tentative:
            self.tentative_tracks[idx].mark_missed(frame_sequence_number=frame_seq, timestamp=timestamp)

        # -------------------------------------------------------------
        # Step 6: Initialize new tracks for unmatched high-confidence detections
        # -------------------------------------------------------------
        new_created_tracks: List[SingleTrack] = []
        for idx in unmatched_high_dets:
            det = remaining_high_dets[idx]
            new_track = SingleTrack(
                track_id=self._get_next_id(),
                detection=det,
                frame_sequence_number=frame_seq,
                min_hits=self.min_hits,
                max_age=self.max_age,
            )
            new_created_tracks.append(new_track)

        # -------------------------------------------------------------
        # Step 7: Update and reorganize track lists
        # -------------------------------------------------------------
        new_tracked: List[SingleTrack] = []
        new_lost: List[SingleTrack] = []
        new_tentative: List[SingleTrack] = []

        # Process confirmed/lost candidates
        for track in track_candidates:
            if track.state == TrackState.CONFIRMED:
                new_tracked.append(track)
            elif track.state == TrackState.LOST:
                new_lost.append(track)
            # REMOVED tracks are dropped

        # Process tentative tracks (promote confirmed ones)
        for track in self.tentative_tracks:
            if track.state == TrackState.CONFIRMED:
                new_tracked.append(track)
            elif track.state == TrackState.TENTATIVE:
                new_tentative.append(track)

        # Include newly created tracks
        for track in new_created_tracks:
            if track.state == TrackState.CONFIRMED:
                new_tracked.append(track)
            elif track.state == TrackState.TENTATIVE:
                new_tentative.append(track)

        self.tracked_tracks = new_tracked
        self.lost_tracks = new_lost
        self.tentative_tracks = new_tentative

        # -------------------------------------------------------------
        # Step 8: Build output TrackedObject list
        # -------------------------------------------------------------
        output_tracks: List[TrackedObject] = []
        for track in self.tracked_tracks:
            output_tracks.append(track.to_schema(timestamp=timestamp))

        if self.return_lost:
            for track in self.lost_tracks:
                output_tracks.append(track.to_schema(timestamp=timestamp))

        return output_tracks

    def _match(
        self,
        tracks: List[SingleTrack],
        detections: List[DetectionRecord],
        max_cost: float,
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Compute IoU cost matrix and solve bipartite matching."""
        if len(tracks) == 0 or len(detections) == 0:
            return [], list(range(len(tracks))), list(range(len(detections)))

        track_boxes = np.array([t.current_bounding_box.to_xyxy() for t in tracks], dtype=np.float32)
        det_boxes = np.array([d.bounding_box.to_xyxy() for d in detections], dtype=np.float32)

        iou_matrix = calculate_iou_matrix(track_boxes, det_boxes)
        cost_matrix = 1.0 - iou_matrix

        return linear_assignment(cost_matrix, max_cost=max_cost)
