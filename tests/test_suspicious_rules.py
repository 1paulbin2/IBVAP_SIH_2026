from analytics.suspicious_rules import is_suspicious_activity


def test_suspicious_activity_when_all_conditions_are_true():
    assert is_suspicious_activity(
        inside_restricted_zone=True,
        night_time=True,
        prolonged_presence=True,
    ) is True


def test_not_suspicious_outside_restricted_zone():
    assert is_suspicious_activity(
        inside_restricted_zone=False,
        night_time=True,
        prolonged_presence=True,
    ) is False


def test_not_suspicious_during_day():
    assert is_suspicious_activity(
        inside_restricted_zone=True,
        night_time=False,
        prolonged_presence=True,
    ) is False


def test_not_suspicious_before_dwell_threshold():
    assert is_suspicious_activity(
        inside_restricted_zone=True,
        night_time=True,
        prolonged_presence=False,
    ) is False