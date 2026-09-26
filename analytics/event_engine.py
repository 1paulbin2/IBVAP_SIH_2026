def create_event(
    event_type,
    camera_id,
    track_id,
    object_type,
    timestamp,
    zone=None,
    severity="MEDIUM",
):
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