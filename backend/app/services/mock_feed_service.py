import json
from pathlib import Path
from typing import List, Dict, Any

MOCK_DATA_DIR = Path(__file__).resolve().parents[3] / "mock_data"

class MockFeedService:
    @staticmethod
    def _load_json(filename: str) -> List[Dict[str, Any]]:
        file_path = MOCK_DATA_DIR / filename
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_frames(cls) -> List[Dict[str, Any]]:
        return cls._load_json("sample_frames.json")

    @classmethod
    def get_detections(cls) -> List[Dict[str, Any]]:
        return cls._load_json("sample_detections.json")

    @classmethod
    def get_tracks(cls) -> List[Dict[str, Any]]:
        return cls._load_json("sample_tracks.json")

    @classmethod
    def get_anpr_records(cls) -> List[Dict[str, Any]]:
        return cls._load_json("sample_anpr.json")

    @classmethod
    def get_events(cls) -> List[Dict[str, Any]]:
        return cls._load_json("sample_events.json")

    @classmethod
    def get_alerts(cls) -> List[Dict[str, Any]]:
        return cls._load_json("sample_alerts.json")
