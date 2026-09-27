"""
Unit tests for TrackPlateAssociator (spatial containment & multi-frame consensus voting).
"""

from datetime import datetime, timezone
import pytest

from schemas.detection import BoundingBox
from schemas.tracking import TrackedObject
from schemas.anpr import PlateRecord, PlateStandard, PlateValidationStatus
from anpr.track_associator import TrackPlateAssociator


def test_spatial_containment_association():
    associator = TrackPlateAssociator(containment_tolerance=10.0)

    # Vehicle track 1 at [100, 100, 400, 400]
    track1 = TrackedObject(
        track_id=1,
        object_class="car",
        bounding_box=BoundingBox(x1=100.0, y1=100.0, x2=400.0, y2=400.0),
        confidence=0.92,
    )
    # Vehicle track 2 at [500, 100, 800, 400]
    track2 = TrackedObject(
        track_id=2,
        object_class="truck",
        bounding_box=BoundingBox(x1=500.0, y1=100.0, x2=800.0, y2=400.0),
        confidence=0.88,
    )

    # Plate located inside vehicle 1 at [200, 300, 300, 350]
    plate_box1 = BoundingBox(x1=200.0, y1=300.0, x2=300.0, y2=350.0)
    matched_id1 = associator.associate_plate_with_tracks(plate_box1, [track1, track2])
    assert matched_id1 == 1

    # Plate located inside vehicle 2 at [600, 320, 700, 360]
    plate_box2 = BoundingBox(x1=600.0, y1=320.0, x2=700.0, y2=360.0)
    matched_id2 = associator.associate_plate_with_tracks(plate_box2, [track1, track2])
    assert matched_id2 == 2

    # Plate completely outside both vehicles
    plate_box_far = BoundingBox(x1=10.0, y1=10.0, x2=50.0, y2=30.0)
    matched_id_none = associator.associate_plate_with_tracks(plate_box_far, [track1, track2])
    assert matched_id_none is None


def test_multi_frame_temporal_voting_consensus():
    associator = TrackPlateAssociator()
    v_track_id = 42

    def make_record(text: str, conf: float, is_valid: bool) -> PlateRecord:
        return PlateRecord(
            plate_text=text,
            raw_text=text,
            plate_confidence=conf,
            vehicle_track_id=v_track_id,
            is_valid_format=is_valid,
            validation_status=PlateValidationStatus.VALID if is_valid else PlateValidationStatus.INVALID_SYNTAX,
            standard=PlateStandard.STANDARD_PRIVATE if is_valid else PlateStandard.UNKNOWN_OR_CUSTOM,
        )

    # Frame 1: Slightly degraded reading
    associator.record_observation(v_track_id, make_record("DL01AB1234", 0.70, True))
    # Frame 2: Glare/noise invalid reading
    associator.record_observation(v_track_id, make_record("DL01AB12", 0.40, False))
    # Frame 3: Sharp crisp reading
    associator.record_observation(v_track_id, make_record("DL01AB1234", 0.95, True))

    consensus = associator.get_consensus_plate(v_track_id)
    assert consensus is not None
    assert consensus.plate_text == "DL01AB1234"
    assert consensus.is_valid_format is True
