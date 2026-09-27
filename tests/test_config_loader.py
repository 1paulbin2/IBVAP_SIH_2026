from rules.config_loader import load_rules_config


def test_load_rules_config():
    config = load_rules_config()

    assert config["dwell_threshold_seconds"] == 60
    assert config["night_start"] == "18:00"
    assert config["night_end"] == "06:00"