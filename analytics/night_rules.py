from datetime import time


def is_night(current_time, night_start, night_end):
    """
    Check whether the given time falls within the configured
    night-time period.

    Supports night periods that cross midnight,
    such as 18:00 to 06:00.
    """

    if night_start <= night_end:
        return night_start <= current_time <= night_end

    return current_time >= night_start or current_time <= night_end