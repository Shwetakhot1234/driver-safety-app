"""Car motion detection using optical flow analysis.

Detects whether the vehicle is in motion or stationary by analyzing
the magnitude of optical flow between consecutive frames.
"""

import cv2
import numpy as np

import config


class MotionDetector:
    """Detects vehicle motion using Farneback optical flow."""

    def __init__(self):
        self._prev_gray = None
        self._motion_magnitude = 0.0
        self.is_moving = False
        self._smoothed_magnitude = 0.0
        self._frame_skip = 0

    def update(self, frame):
        """Update motion state from the current frame.

        Args:
            frame: BGR image (numpy array).

        Returns:
            dict with:
                'is_moving': bool
                'motion_magnitude': float
                'motion_smoothed': float
        """
        # Process every other frame for performance
        self._frame_skip += 1
        if self._frame_skip < 2:
            return {
                'is_moving': self.is_moving,
                'motion_magnitude': self._motion_magnitude,
                'motion_smoothed': self._smoothed_magnitude,
            }
        self._frame_skip = 0

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Resize for faster processing
        small = cv2.resize(gray, (320, 240))

        if self._prev_gray is None:
            self._prev_gray = small
            return {
                'is_moving': False,
                'motion_magnitude': 0.0,
                'motion_smoothed': 0.0,
            }

        # Compute dense optical flow (Farneback)
        flow = cv2.calcOpticalFlowFarneback(
            self._prev_gray, small, None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )

        # Store current frame for next iteration
        self._prev_gray = small

        # Compute magnitude of flow vectors
        magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)

        # Compute mean magnitude (overall scene motion)
        self._motion_magnitude = float(np.mean(magnitude))

        # Smooth the magnitude to avoid flickering
        alpha = 0.3
        self._smoothed_magnitude = (
            alpha * self._motion_magnitude
            + (1 - alpha) * self._smoothed_magnitude
        )

        # Determine if moving
        self.is_moving = (
            self._smoothed_magnitude > config.MOTION_THRESHOLD
        )

        return {
            'is_moving': self.is_moving,
            'motion_magnitude': self._motion_magnitude,
            'motion_smoothed': self._smoothed_magnitude,
        }

    def reset(self):
        """Reset motion detector state."""
        self._prev_gray = None
        self._motion_magnitude = 0.0
        self._smoothed_magnitude = 0.0
        self.is_moving = False
        self._frame_skip = 0
