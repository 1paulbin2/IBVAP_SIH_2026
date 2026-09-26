from analytics.severity import calculate_severity
def create_event(
    event_type,
    camera_id,
    track_id,
    object_type,
    timestamp,
    zone=None,
    severity="MEDIUM",
    evidence_reference=None,
    rule_version="1.0",
):
    """
    Create a standard surveillance event record.
    """

    event_id = f"{camera_id}-{track_id}-{timestamp}"

    return {
        "event_id": event_id,
        "camera_id": camera_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "track_id": track_id,
        "object_type": object_type,
        "zone": zone,
        "severity": severity,
        "evidence_reference": evidence_reference,
        "rule_version": rule_version,
    }
    """
    Create a standard surveillance event record.
    """

    return {
        "event_type": event_type,
        "camera_id": camera_id,
        "track_id": track_id,
        "object_type": object_type,
        "timestamp": timestamp,
        "zone": zone,
        "severity": severity,
    }
def evaluate_track(
    inside_zone,
    night_time,
    dwell_seconds,
    dwell_threshold,
):
    """
    Evaluate a tracked object using explicit surveillance rules.

    Returns True when the object is inside the configured zone,
    it is night-time, and the dwell threshold has been reached.
    """

    if not inside_zone:
        return False

    if not night_time:
        return False

    if dwell_seconds < dwell_threshold:
        return False

    return True
def generate_event(
    camera_id,
    track_id,
    object_type,
    timestamp,
    inside_zone,
    night_time,
    dwell_seconds,
    dwell_threshold,
    zone=None,
):
    """
    Evaluate a track and create an event when all
    configured conditions are satisfied.
    """

    prolonged_presence = dwell_seconds >= dwell_threshold

    should_create_event = evaluate_track(
        inside_zone=inside_zone,
        night_time=night_time,
        dwell_seconds=dwell_seconds,
        dwell_threshold=dwell_threshold,
    )

    if not should_create_event:
        return None

    severity = calculate_severity(
        inside_zone=inside_zone,
        night_time=night_time,
        prolonged_presence=prolonged_presence,
    )

    return create_event(
        event_type="NIGHT_PROLONGED_PRESENCE",
        camera_id=camera_id,
        track_id=track_id,
        object_type=object_type,
        timestamp=timestamp,
        zone=zone,
        severity=severity,
    )