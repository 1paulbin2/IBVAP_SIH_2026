"""
Unit and integration tests for Multi-Object Tracking (ByteTracker + Kalman Filter).
Fulfills Definition of DONE:
- Tracker accepts both real and mock detections.
- Track IDs remain consistent in test scenarios.
- Tests include missed detections and occlusion recovery.
"""

from datetime import datetime, timezone
import pytest

from schemas.detection import BoundingBox, DetectionRecord, FrameDetections
from schemas.tracking import TrackState
from tracking.byte_tracker import ByteTracker


def test_tracker_initialization_and_single_object():
    tracker = ByteTracker(min_hits=1, max_age=5)
    box = BoundingBox(x1=100.0, y1=100.0, x2=200.0, y2=200.0)
    det = DetectionRecord(
        detection_id="d1", class_name="car", confidence=0.9, bounding_box=box
    )
    fd = FrameDetections(camera_id="c1", frame_sequence_number=1, detections=[det])

    tracks = tracker.update(fd)
    assert len(tracks) == 1
    assert tracks[0].track_id == 1
    assert tracks[0].object_class == "car"
    assert tracks[0].hits == 1
    assert tracks[0].state == TrackState.CONFIRMED


def test_tracker_stable_track_ids_across_linear_motion(mock_scenarios):
    """Verify track IDs remain completely consistent across 8 consecutive frames."""
    tracker = ByteTracker(min_hits=1, max_age=10)
    linear_scenario = mock_scenarios["linear_motion"]["frames"]

    seen_track_ids_per_class = {"car": set(), "truck": set()}

    for frame_data in linear_scenario:
        seq = frame_data["frame_seq"]
        dets = [
            DetectionRecord(
                detection_id=d["detection_id"],
                class_name=d["class_name"],
                confidence=d["confidence"],
                bounding_box=BoundingBox(
                    x1=d["bbox"][0], y1=d["bbox"][1], x2=d["bbox"][2], y2=d["bbox"][3]
                ),
            )
            for d in frame_data["detections"]
        ]
        fd = FrameDetections(camera_id="cam1", frame_sequence_number=seq, detections=dets)
        tracks = tracker.update(fd)

        assert len(tracks) == 2
        for t in tracks:
            seen_track_ids_per_class[t.object_class].add(t.track_id)

    # Exactly 1 unique ID for car across all frames, exactly 1 for truck
    assert len(seen_track_ids_per_class["car"]) == 1
    assert len(seen_track_ids_per_class["truck"]) == 1


def test_tracker_handles_temporary_missed_detections_occlusion(mock_scenarios):
    """
    Verify vehicle track survives temporary missed detections (frames 4-5)
    and retains its identical track_id when redetected in frame 6.
    """
    tracker = ByteTracker(min_hits=1, max_age=10, return_lost=True)
    occ_scenario = mock_scenarios["missed_detections_occlusion"]["frames"]

    recorded_track_ids = []

    for frame_data in occ_scenario:
        seq = frame_data["frame_seq"]
        dets = [
            DetectionRecord(
                detection_id=d["detection_id"],
                class_name=d["class_name"],
                confidence=d["confidence"],
                bounding_box=BoundingBox(
                    x1=d["bbox"][0], y1=d["bbox"][1], x2=d["bbox"][2], y2=d["bbox"][3]
                ),
            )
            for d in frame_data["detections"]
        ]
        fd = FrameDetections(camera_id="cam1", frame_sequence_number=seq, detections=dets)
        tracks = tracker.update(fd)

        if seq in (1, 2, 3):
            assert len(tracks) == 1
            assert tracks[0].state == TrackState.CONFIRMED
            recorded_track_ids.append(tracks[0].track_id)
        elif seq in (4, 5):
            # Vehicle missed/occluded: should be retained in lost state
            assert len(tracks) == 1
            assert tracks[0].state == TrackState.LOST
            recorded_track_ids.append(tracks[0].track_id)
        elif seq in (6, 7):
            # Vehicle reappeared: identity MUST be restored!
            assert len(tracks) == 1
            assert tracks[0].state == TrackState.CONFIRMED
            recorded_track_ids.append(tracks[0].track_id)

    # Every single frame must have the exact same track_id
    assert len(set(recorded_track_ids)) == 1
    assert recorded_track_ids[0] == 1


def test_tracker_removes_track_after_max_age():
    """Verify track is pruned once missing frames exceed max_age."""
    tracker = ByteTracker(min_hits=1, max_age=3, return_lost=True)

    # Frame 1: Detection present
    box = BoundingBox(x1=50.0, y1=50.0, x2=150.0, y2=150.0)
    det = DetectionRecord(detection_id="d1", class_name="car", confidence=0.9, bounding_box=box)
    fd1 = FrameDetections(camera_id="cam1", frame_sequence_number=1, detections=[det])
    tracks1 = tracker.update(fd1)
    assert len(tracks1) == 1

    # Frames 2, 3, 4: No detections (missing for 3 frames <= max_age=3)
    for f in range(2, 5):
        fd_empty = FrameDetections(camera_id="cam1", frame_sequence_number=f, detections=[])
        tracks_lost = tracker.update(fd_empty)
        assert len(tracks_lost) == 1
        assert tracks_lost[0].state == TrackState.LOST

    # Frame 5: Missing for 4 frames > max_age=3 -> Track must be deleted
    fd5 = FrameDetections(camera_id="cam1", frame_sequence_number=5, detections=[])
    tracks_empty = tracker.update(fd5)
    assert len(tracks_empty) == 0


def test_tracker_records_trajectory_and_distance():
    tracker = ByteTracker(min_hits=1)
    for i in range(5):
        box = BoundingBox(x1=100.0 + i * 10, y1=100.0, x2=200.0 + i * 10, y2=200.0)
        det = DetectionRecord(detection_id=f"d{i}", class_name="car", confidence=0.9, bounding_box=box)
        fd = FrameDetections(camera_id="cam1", frame_sequence_number=i+1, detections=[det])
        tracks = tracker.update(fd)

    assert len(tracks) == 1
    track = tracks[0]
    assert track.trajectory_length == 5
    assert track.total_distance_traveled() > 35.0
