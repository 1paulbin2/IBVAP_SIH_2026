import os
from src.core.config import DetectionConfig

def test_default_config():
    config = DetectionConfig()
    # Check default values are set
    assert config.conf_threshold == 0.5
    assert config.nms_threshold == 0.45
    assert config.device == "cpu"
    assert config.model_path == "models/yolo_default.pt"
    assert config.input_size == 640

def test_config_env_override(monkeypatch):
    # Mock environment variables
    monkeypatch.setenv("IBVAP_CONF_THRESH", "0.75")
    monkeypatch.setenv("IBVAP_DEVICE", "cuda:0")
    monkeypatch.setenv("IBVAP_MODEL_PATH", "models/custom_yolo.pt")
    
    config = DetectionConfig()
    assert config.conf_threshold == 0.75
    assert config.device == "cuda:0"
    assert config.model_path == "models/custom_yolo.pt"
