def calculate_severity(
    inside_zone,
    night_time,
    prolonged_presence,
):
    """
    Calculate event severity using explicit, explainable conditions.
    """

    if inside_zone and night_time and prolonged_presence:
        return "CRITICAL"

    if inside_zone and night_time:
        return "HIGH"

    if inside_zone:
        return "MEDIUM"

    return "LOW"