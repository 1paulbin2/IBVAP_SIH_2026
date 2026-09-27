import json
from pathlib import Path


CONFIG_PATH = Path(__file__).parent / "rules_config.json"


def load_rules_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)