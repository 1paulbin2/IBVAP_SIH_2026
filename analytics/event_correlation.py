from datetime import datetime


def is_duplicate_event(
    previous_event,
    current_event,
    correlation_window_seconds,
):
    """
    Check whether two events should be treated as duplicates.

    Events are duplicates when:
    - they belong to the same camera
    - they belong to the same track
    - they have the same event type
    - they occur within the configured time window
    """

    if previous_event["camera_id"] != current_event["camera_id"]:
        return False

    if previous_event["track_id"] != current_event["track_id"]:
        return False

    if previous_event["event_type"] != current_event["event_type"]:
        return False

    previous_time = datetime.fromisoformat(previous_event["timestamp"])
    current_time = datetime.fromisoformat(current_event["timestamp"])

    time_difference = abs(
        (current_time - previous_time).total_seconds()
    )

    return time_difference <= correlation_window_seconds