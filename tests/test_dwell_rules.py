from analytics.dwell_rules import is_prolonged_presence


def test_below_threshold():
    assert is_prolonged_presence(30, 60) is False


def test_at_threshold():
    assert is_prolonged_presence(60, 60) is True


def test_above_threshold():
    assert is_prolonged_presence(90, 60) is True