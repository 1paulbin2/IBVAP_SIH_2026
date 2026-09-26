from analytics.event_engine import create_event


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