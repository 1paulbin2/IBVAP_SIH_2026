def is_suspicious_activity(
    inside_restricted_zone,
    night_time,
    prolonged_presence,
):
    """
    Determine whether an explicit set of conditions
    indicates a suspicious-activity event.

    All conditions must be true:
    - object is inside a restricted zone
    - it is night-time
    - object has remained for the configured dwell threshold
    """

    if not inside_restricted_zone:
        return False

    if not night_time:
        return False

    if not prolonged_presence:
        return False

    return True