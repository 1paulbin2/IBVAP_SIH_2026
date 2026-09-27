from datetime import time

from analytics.night_rules import is_night


def test_night_time_after_start():
    assert is_night(
        time(23, 0),
        time(18, 0),
        time(6, 0)
    ) is True


def test_night_time_before_end():
    assert is_night(
        time(3, 0),
        time(18, 0),
        time(6, 0)
    ) is True


def test_day_time():
    assert is_night(
        time(12, 0),
        time(18, 0),
        time(6, 0)
    ) is False
    
def test_night_boundary_times():
    assert is_night(
        time(18, 0),
        time(18, 0),
        time(6, 0)
    ) is True

    assert is_night(
        time(6, 0),
        time(18, 0),
        time(6, 0)
    ) is True