"""Distraction detection using nose direction and gaze deviation.

Detects distraction when the driver is NOT looking at the camera.
Also detects mobile phone usage when the driver is looking down
with eyes still open (not drowsy).

States:
- NORMAL: Looking at the camera (forward)
- DISTRACTED: Head turned away or eyes looking sideways
- PHONE_USAGE: Looking down with eyes open (likely using phone)
"""

import numpy as np

from detector.utils import (
    NOSE_TIP,
    CHIN,
    LEFT_EYE_OUTER,
    RIGHT_EYE_OUTER,
    LEFT_IRIS,
    RIGHT_IRIS,
    LEFT_EYE_BOUNDARY,
    RIGHT_EYE_BOUNDARY,
    FOREHEAD_GLABELLA,
    get_landmark_coords,
)
import config


class DistractionDetector:
    """Detects driver distraction including mobile phone usage.

    Detects three states:
    1. Head turned away (left/right) or gaze off-center
    2. Mobile phone usage (looking down with eyes open)
    3. Normal (looking at the camera/road)
    """

    def __init__(self):
        self.distraction_counter = 0
        self.phone_counter = 0
        self.is_distracted = False
        self.is_phone_usage = False
        self.head_yaw_ratio = 0.0
        self.head_pitch_ratio = 0.0
        self.gaze_horizontal = 0.0
        self.gaze_vertical = 0.0
        self.looking_at_camera = True

    def _compute_head_direction(self, landmarks, frame_w, frame_h):
        """Compute head direction using nose position relative to face center.

        Returns:
            Tuple of (yaw_ratio, pitch_ratio).
            yaw_ratio: positive = looking right, negative = looking left
            pitch_ratio: positive = looking up, negative = looking down
        """
        nose = np.array([landmarks[NOSE_TIP].x, landmarks[NOSE_TIP].y])
        chin = np.array([landmarks[CHIN].x, landmarks[CHIN].y])
        left_eye = np.array([landmarks[LEFT_EYE_OUTER].x, landmarks[LEFT_EYE_OUTER].y])
        right_eye = np.array([landmarks[RIGHT_EYE_OUTER].x, landmarks[RIGHT_EYE_OUTER].y])
        forehead = np.array([landmarks[FOREHEAD_GLABELLA].x, landmarks[FOREHEAD_GLABELLA].y])

        eye_mid = (left_eye + right_eye) / 2.0
        face_width = np.linalg.norm(right_eye - left_eye)

        if face_width < 0.001:
            return 0.0, 0.0

        yaw_ratio = (nose[0] - eye_mid[0]) / face_width

        face_center_y = (forehead[1] + chin[1]) / 2.0
        face_height = abs(chin[1] - forehead[1])

        if face_height < 0.001:
            return yaw_ratio, 0.0

        # Negative = nose below center = looking down
        pitch_ratio = (face_center_y - nose[1]) / face_height

        return float(yaw_ratio), float(pitch_ratio)

    def _compute_gaze_direction(self, landmarks, frame_w, frame_h):
        """Compute both horizontal and vertical gaze direction.

        Returns:
            Tuple of (gaze_horizontal, gaze_vertical).
            gaze_horizontal: ~0 when looking forward, +/- when looking sideways
            gaze_vertical: ~0 when looking forward, negative when looking down
        """
        try:
            # Get iris centers
            left_iris = np.array([landmarks[LEFT_IRIS[0]].x, landmarks[LEFT_IRIS[0]].y])
            right_iris = np.array([landmarks[RIGHT_IRIS[0]].x, landmarks[RIGHT_IRIS[0]].y])

            # Get eye boundary points
            left_eye_pts = get_landmark_coords(landmarks, LEFT_EYE_BOUNDARY, frame_w, frame_h)
            right_eye_pts = get_landmark_coords(landmarks, RIGHT_EYE_BOUNDARY, frame_w, frame_h)

            # --- Horizontal gaze ---
            left_min_x, left_max_x = left_eye_pts[:, 0].min(), left_eye_pts[:, 0].max()
            left_center_x = (left_min_x + left_max_x) / 2.0
            left_width = left_max_x - left_min_x

            if left_width > 1.0:
                left_h_offset = (left_iris[0] * frame_w - left_center_x) / left_width
            else:
                left_h_offset = 0.0

            right_min_x, right_max_x = right_eye_pts[:, 0].min(), right_eye_pts[:, 0].max()
            right_center_x = (right_min_x + right_max_x) / 2.0
            right_width = right_max_x - right_min_x

            if right_width > 1.0:
                right_h_offset = (right_iris[0] * frame_w - right_center_x) / right_width
            else:
                right_h_offset = 0.0

            gaze_h = (left_h_offset + right_h_offset) / 2.0

            # --- Vertical gaze (looking down = negative) ---
            left_min_y, left_max_y = left_eye_pts[:, 1].min(), left_eye_pts[:, 1].max()
            left_center_y = (left_min_y + left_max_y) / 2.0
            left_height = left_max_y - left_min_y

            if left_height > 1.0:
                left_v_offset = (left_center_y - left_iris[1] * frame_h) / left_height
            else:
                left_v_offset = 0.0

            right_min_y, right_max_y = right_eye_pts[:, 1].min(), right_eye_pts[:, 1].max()
            right_center_y = (right_min_y + right_max_y) / 2.0
            right_height = right_max_y - right_min_y

            if right_height > 1.0:
                right_v_offset = (right_center_y - right_iris[1] * frame_h) / right_height
            else:
                right_v_offset = 0.0

            gaze_v = (left_v_offset + right_v_offset) / 2.0

            return float(gaze_h), float(gaze_v)

        except (IndexError, ValueError, ZeroDivisionError):
            return 0.0, 0.0

    def update(self, landmarks, frame_w, frame_h, ear=0.3, phone_in_frame=False):
        """Update distraction state from current frame landmarks.

        Detects:
        - DISTRACTED: Head turned sideways or gaze off-center
        - PHONE_USAGE: Looking down + eyes open + phone visible in camera
        - NORMAL: Looking at the camera

        Args:
            landmarks: List of NormalizedLandmark objects.
            frame_w: Frame width in pixels.
            frame_h: Frame height in pixels.
            ear: Current Eye Aspect Ratio (to distinguish phone use from drowsiness).
            phone_in_frame: Whether a phone object was detected in the frame.

        Returns:
            dict with distraction state information.
        """
        # Compute head direction
        self.head_yaw_ratio, self.head_pitch_ratio = self._compute_head_direction(
            landmarks, frame_w, frame_h
        )

        # Compute gaze direction (both horizontal and vertical)
        self.gaze_horizontal, self.gaze_vertical = self._compute_gaze_direction(
            landmarks, frame_w, frame_h
        )

        # --- Detect head turned sideways ---
        is_head_turned = (
            abs(self.head_yaw_ratio) > config.HEAD_YAW_RATIO_THRESHOLD
        )

        # --- Detect gaze off-center (looking sideways) ---
        is_gaze_away = abs(self.gaze_horizontal) > config.GAZE_RATIO_THRESHOLD

        # --- Detect mobile phone usage ---
        is_looking_down = (
            self.head_pitch_ratio < -config.PHONE_PITCH_RATIO_THRESHOLD or
            self.gaze_vertical < -config.PHONE_GAZE_VERTICAL_THRESHOLD
        )
        is_eyes_open = ear >= config.EAR_THRESHOLD

        is_phone_behavior = is_looking_down and is_eyes_open
        self.is_phone_usage = is_phone_behavior and phone_in_frame

        # --- Determine if looking at camera ---
        self.looking_at_camera = (
            not is_head_turned and
            not is_gaze_away and
            not self.is_phone_usage
        )

        # --- Count consecutive distraction frames ---
        if is_head_turned or is_gaze_away:
            self.distraction_counter += 1
        else:
            self.distraction_counter = max(0, self.distraction_counter - 2)

        self.is_distracted = (
            self.distraction_counter >= config.CONSECUTIVE_FRAMES_DISTRACTED
            and not self.is_phone_usage  # Phone takes priority over distraction
        )

        # Count consecutive phone usage frames
        if self.is_phone_usage:
            self.phone_counter += 1
        else:
            self.phone_counter = max(0, self.phone_counter - 2)

        self.is_phone_usage = (
            self.phone_counter >= config.CONSECUTIVE_FRAMES_PHONE
        )

        return {
            'head_yaw_ratio': self.head_yaw_ratio,
            'head_pitch_ratio': self.head_pitch_ratio,
            'gaze_horizontal': self.gaze_horizontal,
            'gaze_vertical': self.gaze_vertical,
            'looking_at_camera': self.looking_at_camera,
            'is_distracted': self.is_distracted,
            'is_phone_usage': self.is_phone_usage,
        }

    def reset(self):
        """Reset all counters and states."""
        self.distraction_counter = 0
        self.phone_counter = 0
        self.is_distracted = False
        self.is_phone_usage = False
        self.head_yaw_ratio = 0.0
        self.head_pitch_ratio = 0.0
        self.gaze_horizontal = 0.0
        self.gaze_vertical = 0.0
        self.looking_at_camera = True
