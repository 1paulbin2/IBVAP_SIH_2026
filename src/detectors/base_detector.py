from abc import ABC, abstractmethod
from typing import List
import numpy as np

from src.api.detection_interface import DetectionResult

class BaseDetector(ABC):
    """
    Abstract base class for all AI detectors in the IBVAP system.
    Enforces a consistent input/output interface for downstream modules
    like Object Tracking and ANPR.
    """
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Perform detection on a single image frame.
        
        Args:
            frame: A numpy array representing the image. 
                   Typically expected in BGR format as read by cv2.imread().
                   
        Returns:
            A list of DetectionResult objects.
        """
        pass
