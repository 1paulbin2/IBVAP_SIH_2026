from analytics.event_engine import create_event, evaluate_track


def test_create_event():
    event = create_event(
        event_type="NIGHT_PROLONGED_PRESENCE",
        camera_id="CAM01",
        track_id=27,
        object_type="person",
        timestamp="2026-09-25T23:15:00",
        zone="BORDER_ZONE_A",
        severity="HIGH",
    )

    assert event["event_type"] == "NIGHT_PROLONGED_PRESENCE"
    assert event["camera_id"] == "CAM01"
    assert event["track_id"] == 27
    assert event["object_type"] == "person"
    assert event["zone"] == "BORDER_ZONE_A"
    assert event["severity"] == "HIGH"
def test_evaluate_track_triggers_event():
    result = evaluate_track(
        inside_zone=True,
        night_time=True,
        dwell_seconds=90,
        dwell_threshold=60,
    )

    assert result is True


def test_evaluate_track_no_event_outside_zone():
    result = evaluate_track(
        inside_zone=False,
        night_time=True,
        dwell_seconds=90,
        dwell_threshold=60,
    )

    assert result is False


def test_evaluate_track_no_event_during_day():
    result = evaluate_track(
        inside_zone=True,
        night_time=False,
        dwell_seconds=90,
        dwell_threshold=60,
    )

    assert result is False


def test_evaluate_track_no_event_before_dwell_threshold():
    result = evaluate_track(
        inside_zone=True,
        night_time=True,
        dwell_seconds=30,
        dwell_threshold=60,
    )

    assert result is False