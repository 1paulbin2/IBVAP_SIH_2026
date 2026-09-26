from datetime import time

from analytics.night_rules import is_night
from analytics.dwell_rules import is_prolonged_presence
from analytics.suspicious_rules import is_suspicious_activity
from analytics.severity import calculate_severity
from analytics.event_engine import generate_event
from rules.config_loader import load_rules_config


def test_full_analytics_flow():
    config = load_rules_config()

    current_time = time(23, 15)

    inside_zone = True
    dwell_seconds = 90

    night_start = time.fromisoformat(config["night_start"])
    night_end = time.fromisoformat(config["night_end"])

    night_time = is_night(
        current_time,
        night_start,
        night_end,
    )

    prolonged_presence = is_prolonged_presence(
        dwell_seconds,
        config["dwell_threshold_seconds"],
    )

    suspicious = is_suspicious_activity(
        inside_restricted_zone=inside_zone,
        night_time=night_time,
        prolonged_presence=prolonged_presence,
    )

    severity = calculate_severity(
        inside_zone=inside_zone,
        night_time=night_time,
        prolonged_presence=prolonged_presence,
    )

    event = generate_event(
        camera_id="CAM01",
        track_id=27,
        object_type="person",
        timestamp="2026-09-26T23:15:00",
        inside_zone=inside_zone,
        night_time=night_time,
        dwell_seconds=dwell_seconds,
        dwell_threshold=config["dwell_threshold_seconds"],
        zone="BORDER_ZONE_A",
    )

    assert night_time is True
    assert prolonged_presence is True
    assert suspicious is True
    assert severity == "CRITICAL"

    assert event is not None
    assert event["event_type"] == "NIGHT_PROLONGED_PRESENCE"
    assert event["severity"] == "CRITICAL"
    assert event["camera_id"] == "CAM01"
    assert event["track_id"] == 27
    assert event["zone"] == "BORDER_ZONE_A"