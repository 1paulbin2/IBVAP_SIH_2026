import os
from dataclasses import dataclass, field

@dataclass
class DetectionConfig:
    """
    Configuration parameters for the AI Detection module.
    Values can be overridden using environment variables.
    """
    # Model parameters
    model_path: str = field(default_factory=lambda: os.getenv("IBVAP_MODEL_PATH", "models/yolo_default.pt"))
    device: str = field(default_factory=lambda: os.getenv("IBVAP_DEVICE", "cpu"))
    
    # Detection thresholds
    conf_threshold: float = field(default_factory=lambda: float(os.getenv("IBVAP_CONF_THRESH", 0.5)))
    nms_threshold: float = field(default_factory=lambda: float(os.getenv("IBVAP_NMS_THRESH", 0.45)))
    
    # Input settings
    input_size: int = field(default_factory=lambda: int(os.getenv("IBVAP_INPUT_SIZE", 640)))
