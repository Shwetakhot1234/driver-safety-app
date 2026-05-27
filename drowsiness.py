"""Drowsiness detection using Eye Aspect Ratio (EAR) and Mouth Aspect Ratio (MAR)."""

import numpy as np

from detector.utils import (
    LEFT_EYE,
    RIGHT_EYE,
    MOUTH_TOP,
    MOUTH_BOTTOM,
    MOUTH_LEFT,
    MOUTH_RIGHT,
    MOUTH_UPPER_LEFT,
    MOUTH_UPPER_RIGHT,
    MOUTH_LOWER_LEFT,
    MOUTH_LOWER_RIGHT,
    get_landmark_coords,
    euclidean_distance,
)
import config


class DrowsinessDetector:
    """Detects drowsiness by monitoring eye closure and yawning.

    Provides two levels of eye closure detection:
    - 'eyes_closed': Eyes closed for ~1 second (early warning beep)
    - 'is_drowsy': Eyes closed for ~2 seconds (full drowsy alert)
    """

    def __init__(self):
        self.ear_counter = 0
        self.mar_counter = 0
        self.is_drowsy = False
        self.is_yawning = False
        self.eyes_closed = False  # Early warning: eyes closed for ~1 second

    @staticmethod
    def compute_ear(eye_points):
        """Compute Eye Aspect Ratio for a single eye.

        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)

        Args:
            eye_points: numpy array of shape (6, 2) with the 6 eye landmarks.

        Returns:
            Float EAR value. Normal open eye ~0.30, closed eye ~0.05-0.15.
        """
        # Vertical distances
        vertical_1 = euclidean_distance(eye_points[1], eye_points[5])
        vertical_2 = euclidean_distance(eye_points[2], eye_points[4])
        # Horizontal distance
        horizontal = euclidean_distance(eye_points[0], eye_points[3])

        if horizontal == 0:
            return 0.0

        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear

    @staticmethod
    def compute_mar(landmarks, frame_w, frame_h):
        """Compute Mouth Aspect Ratio using multiple landmark pairs for robustness.

        Uses 3 vertical measurements across the mouth and normalizes by
        the horizontal mouth width.

        MAR = (vert1 + vert2 + vert3) / (3 * horizontal)

        Args:
            landmarks: List of NormalizedLandmark objects.
            frame_w: Frame width in pixels.
            frame_h: Frame height in pixels.

        Returns:
            Float MAR value. Normal closed ~0.05-0.15, yawning ~0.4-0.8+.
        """
        # Get all mouth landmark positions
        top = np.array([landmarks[MOUTH_TOP].x * frame_w,
                        landmarks[MOUTH_TOP].y * frame_h])
        bottom = np.array([landmarks[MOUTH_BOTTOM].x * frame_w,
                           landmarks[MOUTH_BOTTOM].y * frame_h])
        left = np.array([landmarks[MOUTH_LEFT].x * frame_w,
                         landmarks[MOUTH_LEFT].y * frame_h])
        right = np.array([landmarks[MOUTH_RIGHT].x * frame_w,
                          landmarks[MOUTH_RIGHT].y * frame_h])
        upper_left = np.array([landmarks[MOUTH_UPPER_LEFT].x * frame_w,
                               landmarks[MOUTH_UPPER_LEFT].y * frame_h])
        upper_right = np.array([landmarks[MOUTH_UPPER_RIGHT].x * frame_w,
                                landmarks[MOUTH_UPPER_RIGHT].y * frame_h])
        lower_left = np.array([landmarks[MOUTH_LOWER_LEFT].x * frame_w,
                               landmarks[MOUTH_LOWER_LEFT].y * frame_h])
        lower_right = np.array([landmarks[MOUTH_LOWER_RIGHT].x * frame_w,
                                landmarks[MOUTH_LOWER_RIGHT].y * frame_h])

        # Horizontal mouth width
        horizontal = euclidean_distance(left, right)
        if horizontal == 0:
            return 0.0

        # Three vertical measurements across the mouth
        vert_center = euclidean_distance(top, bottom)           # Center
        vert_left = euclidean_distance(upper_left, lower_left)  # Left third
        vert_right = euclidean_distance(upper_right, lower_right)  # Right third

        # Average vertical opening normalized by mouth width
        mar = (vert_center + vert_left + vert_right) / (3.0 * horizontal)
        return mar

    def update(self, landmarks, frame_w, frame_h):
        """Update drowsiness state from current frame landmarks.

        Args:
            landmarks: List of NormalizedLandmark objects from MediaPipe Tasks API.
            frame_w: Frame width in pixels.
            frame_h: Frame height in pixels.

        Returns:
            dict with keys:
                'ear': average EAR value
                'mar': MAR value
                'is_drowsy': bool - eyes closed for too long
                'is_yawning': bool - mouth open (yawning) for too long
        """
        # Compute EAR for both eyes
        left_eye_pts = get_landmark_coords(landmarks, LEFT_EYE, frame_w, frame_h)
        right_eye_pts = get_landmark_coords(landmarks, RIGHT_EYE, frame_w, frame_h)

        left_ear = self.compute_ear(left_eye_pts)
        right_ear = self.compute_ear(right_eye_pts)
        avg_ear = (left_ear + right_ear) / 2.0

        # Compute MAR using improved multi-point calculation
        mar = self.compute_mar(landmarks, frame_w, frame_h)

        # Check drowsiness (eyes closed)
        if avg_ear < config.EAR_THRESHOLD:
            self.ear_counter += 1
        else:
            self.ear_counter = 0

        # Early warning: eyes closed for ~1 second (30 frames at 30fps)
        self.eyes_closed = self.ear_counter >= 30
        # Full drowsy: eyes closed for ~2 seconds (60 frames at 30fps)
        self.is_drowsy = self.ear_counter >= config.CONSECUTIVE_FRAMES_DROWSY

        # Check yawning (mouth open wide)
        if mar > config.MAR_THRESHOLD:
            self.mar_counter += 1
        else:
            self.mar_counter = max(0, self.mar_counter - 1)  # Slow decay

        self.is_yawning = self.mar_counter >= config.CONSECUTIVE_FRAMES_YAWN

        return {
            'ear': avg_ear,
            'mar': mar,
            'is_drowsy': self.is_drowsy,
            'is_yawning': self.is_yawning,
            'eyes_closed': self.eyes_closed,  # Early warning
        }

    def reset(self):
        """Reset all counters and states."""
        self.ear_counter = 0
        self.mar_counter = 0
        self.is_drowsy = False
        self.is_yawning = False
        self.eyes_closed = False
