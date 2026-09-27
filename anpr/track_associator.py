"""
Vehicle track association and multi-frame temporal voting for ANPR.
Associates recognized plates with active vehicle track IDs and accumulates observations
to achieve consensus across consecutive video frames.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from schemas.detection import BoundingBox
from schemas.tracking import TrackedObject
from schemas.anpr import PlateRecord


class TrackPlateAssociator:
    """
    Associates detected plate regions with vehicle tracks and performs multi-frame voting.
    """

    def __init__(self, containment_tolerance: float = 15.0):
        self.containment_tolerance = containment_tolerance
        # track_id -> List[PlateRecord]
        self._track_history: Dict[int, List[PlateRecord]] = defaultdict(list)

    def associate_plate_with_tracks(
        self,
        plate_box: BoundingBox,
        tracks: List[TrackedObject],
    ) -> Optional[int]:
        """
        Find the track_id of the vehicle whose bounding box encloses this plate bounding box.
        If multiple overlap, chooses the vehicle with the highest containment / smallest enclosing area.
        """
        best_track_id: Optional[int] = None
        best_enclosure_ratio: float = 0.0

        for track in tracks:
            v_box = track.bounding_box
            # Check if plate box is inside vehicle box
            if v_box.contains(plate_box, tolerance=self.containment_tolerance):
                # Calculate intersection ratio: plate_area_inside / total_plate_area
                ix1 = max(v_box.x1, plate_box.x1)
                iy1 = max(v_box.y1, plate_box.y1)
                ix2 = min(v_box.x2, plate_box.x2)
                iy2 = min(v_box.y2, plate_box.y2)

                iw = max(0.0, ix2 - ix1)
                ih = max(0.0, iy2 - iy1)
                intersect_area = iw * ih
                ratio = intersect_area / max(plate_box.area, 1e-5)

                if ratio > best_enclosure_ratio and ratio >= 0.7:
                    best_enclosure_ratio = ratio
                    best_track_id = track.track_id

        return best_track_id

    def record_observation(self, track_id: int, plate_record: PlateRecord) -> None:
        """Register a new plate observation for a specific vehicle track."""
        plate_record.vehicle_track_id = track_id
        self._track_history[track_id].append(plate_record)

    def get_consensus_plate(self, track_id: int) -> Optional[PlateRecord]:
        """
        Select the best, most consistent plate reading for a given vehicle track.
        Valid plates strictly outrank invalid syntax; higher confidence breaks ties.
        """
        history = self._track_history.get(track_id, [])
        if not history:
            return None

        # Filter valid plates
        valid_records = [p for p in history if p.is_valid_format and p.plate_text]
        if valid_records:
            # Group by plate_text and sum confidence
            votes: Dict[str, float] = defaultdict(float)
            record_map: Dict[str, PlateRecord] = {}

            for p in valid_records:
                votes[p.plate_text] += p.plate_confidence
                # Keep latest/highest single record
                if p.plate_text not in record_map or p.plate_confidence > record_map[p.plate_text].plate_confidence:
                    record_map[p.plate_text] = p

            # Best text by accumulated confidence
            best_text = max(votes.keys(), key=lambda k: votes[k])
            return record_map[best_text]

        # If no valid records, return the highest confidence invalid observation
        return max(history, key=lambda p: p.plate_confidence)

    def prune_old_tracks(self, active_track_ids: List[int], max_idle_history: int = 100) -> None:
        """Prune tracks that are no longer active to prevent memory bloat."""
        active_set = set(active_track_ids)
        to_delete = [tid for tid in self._track_history if tid not in active_set and len(self._track_history[tid]) > max_idle_history]
        for tid in to_delete:
            del self._track_history[tid]
