from analytics.severity import calculate_severity


def test_critical_severity():
    assert calculate_severity(
        inside_zone=True,
        night_time=True,
        prolonged_presence=True,
    ) == "CRITICAL"


def test_high_severity():
    assert calculate_severity(
        inside_zone=True,
        night_time=True,
        prolonged_presence=False,
    ) == "HIGH"


def test_medium_severity():
    assert calculate_severity(
        inside_zone=True,
        night_time=False,
        prolonged_presence=False,
    ) == "MEDIUM"


def test_low_severity():
    assert calculate_severity(
        inside_zone=False,
        night_time=False,
        prolonged_presence=False,
    ) == "LOW"