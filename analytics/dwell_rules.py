def is_prolonged_presence(dwell_seconds, threshold_seconds):
    """
    Check whether an object has remained in an area
    longer than the configured dwell-time threshold.
    """

    return dwell_seconds >= threshold_seconds