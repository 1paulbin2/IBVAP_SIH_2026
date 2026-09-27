"""
Kalman Filter implementation for bounding box tracking in image coordinate space.
Follows the standard state formulation: [cx, cy, a, h, vx, vy, va, vh]
where (cx, cy) is box center, 'a' is aspect ratio (w/h), 'h' is height, and (vx, vy, va, vh) are velocities.
"""

from __future__ import annotations
from typing import Tuple
import numpy as np


class KalmanBoxTracker:
    """
    Kalman filter tracking a single bounding box with constant velocity motion model.
    """

    def __init__(self, bbox_xyxy: Tuple[float, float, float, float]):
        """
        Initialize Kalman filter with an initial bounding box [x1, y1, x2, y2].
        """
        # State vector dimension: 8 (x, y, a, h, vx, vy, va, vh)
        self.dim_x = 8
        # Measurement vector dimension: 4 (x, y, a, h)
        self.dim_z = 4

        # State transition matrix F
        self.F = np.eye(self.dim_x, dtype=np.float32)
        for i in range(4):
            self.F[i, i + 4] = 1.0  # pos += vel * dt (dt = 1)

        # Measurement matrix H
        self.H = np.zeros((self.dim_z, self.dim_x), dtype=np.float32)
        for i in range(4):
            self.H[i, i] = 1.0

        # State vector x
        self.x = np.zeros((self.dim_x, 1), dtype=np.float32)
        z = self.xyxy_to_z(bbox_xyxy)
        self.x[:4] = z

        # Covariance matrix P
        self.P = np.diag([10.0, 10.0, 10.0, 10.0, 100.0, 100.0, 100.0, 100.0]).astype(np.float32)

        # Process noise covariance Q
        self.Q = np.diag([1.0, 1.0, 1.0, 1.0, 0.01, 0.01, 0.001, 0.01]).astype(np.float32)

        # Measurement noise covariance R
        self.R = np.diag([1.0, 1.0, 10.0, 10.0]).astype(np.float32)

    @staticmethod
    def xyxy_to_z(xyxy: Tuple[float, float, float, float]) -> np.ndarray:
        """
        Convert [x1, y1, x2, y2] to measurement vector [cx, cy, a, h].
        """
        x1, y1, x2, y2 = xyxy
        w = max(1e-4, x2 - x1)
        h = max(1e-4, y2 - y1)
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        a = w / h
        return np.array([[cx], [cy], [a], [h]], dtype=np.float32)

    @staticmethod
    def z_to_xyxy(z: np.ndarray) -> Tuple[float, float, float, float]:
        """
        Convert state/measurement [cx, cy, a, h] to [x1, y1, x2, y2].
        """
        cx = float(z[0, 0])
        cy = float(z[1, 0])
        a = max(1e-4, float(z[2, 0]))
        h = max(1e-4, float(z[3, 0]))
        w = max(1e-4, a * h)

        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        x2 = cx + w / 2.0
        y2 = cy + h / 2.0
        return (x1, y1, x2, y2)

    def predict(self) -> Tuple[float, float, float, float]:
        """
        Advances the state vector and returns the predicted bounding box [x1, y1, x2, y2].
        """
        # If height or aspect ratio are degenerate, bound them
        if (self.x[6, 0] + self.x[2, 0]) <= 0:
            self.x[6, 0] = 0.0

        # x = F * x
        self.x = np.dot(self.F, self.x)
        # P = F * P * F^T + Q
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        return self.z_to_xyxy(self.x[:4])

    def update(self, bbox_xyxy: Tuple[float, float, float, float]) -> None:
        """
        Updates the state vector with observed bounding box [x1, y1, x2, y2].
        """
        z = self.xyxy_to_z(bbox_xyxy)
        # Innovation: y = z - H * x
        y = z - np.dot(self.H, self.x)
        # Innovation covariance: S = H * P * H^T + R
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        # Kalman gain: K = P * H^T * inv(S)
        try:
            S_inv = np.linalg.inv(S)
        except np.linalg.LinAlgError:
            S_inv = np.linalg.pinv(S)
        K = np.dot(np.dot(self.P, self.H.T), S_inv)

        # State update: x = x + K * y
        self.x = self.x + np.dot(K, y)
        # Covariance update: P = (I - K * H) * P
        I = np.eye(self.dim_x, dtype=np.float32)
        I_KH = I - np.dot(K, self.H)
        # Joseph form for numerical stability
        self.P = np.dot(np.dot(I_KH, self.P), I_KH.T) + np.dot(np.dot(K, self.R), K.T)

    @property
    def current_xyxy(self) -> Tuple[float, float, float, float]:
        """Return current estimated bounding box [x1, y1, x2, y2]."""
        return self.z_to_xyxy(self.x[:4])

    @property
    def velocity(self) -> Tuple[float, float]:
        """Return (vx, vy) in pixels/frame."""
        return (float(self.x[4, 0]), float(self.x[5, 0]))
