from analytics.event_correlation import is_duplicate_event


def test_duplicate_event_within_time_window():
    previous_event = {
        "camera_id": "CAM01",
        "track_id": 27,
        "event_type": "NIGHT_PROLONGED_PRESENCE",
        "timestamp": "2026-09-25T23:15:00",
    }

    current_event = {
        "camera_id": "CAM01",
        "track_id": 27,
        "event_type": "NIGHT_PROLONGED_PRESENCE",
        "timestamp": "2026-09-25T23:15:30",
    }

    assert is_duplicate_event(
        previous_event,
        current_event,
        correlation_window_seconds=60,
    ) is True


def test_not_duplicate_for_different_track():
    previous_event = {
        "camera_id": "CAM01",
        "track_id": 27,
        "event_type": "NIGHT_PROLONGED_PRESENCE",
        "timestamp": "2026-09-25T23:15:00",
    }

    current_event = {
        "camera_id": "CAM01",
        "track_id": 28,
        "event_type": "NIGHT_PROLONGED_PRESENCE",
        "timestamp": "2026-09-25T23:15:30",
    }

    assert is_duplicate_event(
        previous_event,
        current_event,
        correlation_window_seconds=60,
    ) is False


def test_not_duplicate_outside_time_window():
    previous_event = {
        "camera_id": "CAM01",
        "track_id": 27,
        "event_type": "NIGHT_PROLONGED_PRESENCE",
        "timestamp": "2026-09-25T23:15:00",
    }

    current_event = {
        "camera_id": "CAM01",
        "track_id": 27,
        "event_type": "NIGHT_PROLONGED_PRESENCE",
        "timestamp": "2026-09-25T23:17:00",
    }

    assert is_duplicate_event(
        previous_event,
        current_event,
        correlation_window_seconds=60,
    ) is False