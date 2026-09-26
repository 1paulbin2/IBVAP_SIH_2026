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