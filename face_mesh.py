"""MediaPipe FaceLandmarker wrapper for facial landmark detection (Tasks API).

Adapted for the mobile app - uses config.FACE_MODEL_PATH for model location.
"""

import cv2
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[WARNING] MediaPipe not available. Face detection disabled.")

import config


class FaceMeshDetector:
    """Wraps MediaPipe FaceLandmarker (Tasks API) to detect facial landmarks."""

    def __init__(self, model_path=None, max_num_faces=1,
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        if not MEDIAPIPE_AVAILABLE:
            print("[WARNING] MediaPipe not installed. FaceMeshDetector disabled.")
            self._landmarker = None
            return

        self.max_num_faces = max_num_faces
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        # Resolve model path from config
        if model_path is None:
            model_path = config.FACE_MODEL_PATH

        if not config.FACE_MODEL_PATH and not model_path:
            raise FileNotFoundError(
                "Face landmarker model path not configured. "
                "Set FACE_MODEL_PATH in config.py"
            )

        if model_path and not __import__('os').path.exists(model_path):
            print(f"[WARNING] Face landmarker model not found at: {model_path}")
            print("[WARNING] Face mesh detection will not work.")

        # Create FaceLandmarker using IMAGE mode
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=max_num_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_tracking_confidence,
            min_tracking_confidence=min_tracking_confidence,
            running_mode=vision.RunningMode.IMAGE,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def process(self, frame):
        """Process a BGR frame and return face landmarks."""
        if self._landmarker is None:
            return None

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self._landmarker.detect(mp_image)

        if result.face_landmarks:
            return result.face_landmarks
        return None

    def draw_landmarks(self, frame, face_landmarks):
        """Draw face mesh landmarks on the frame.

        Args:
            frame: BGR numpy array.
            face_landmarks: List of NormalizedLandmark objects.

        Returns:
            Frame with landmarks drawn.
        """
        h, w = frame.shape[:2]

        # Draw all landmarks as small circles
        for lm in face_landmarks:
            x = int(lm.x * w)
            y = int(lm.y * h)
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # Draw eye contours
        left_eye_indices = [33, 160, 158, 133, 33]
        right_eye_indices = [362, 385, 387, 263, 362]
        mouth_indices = [61, 291, 14, 13, 61]

        for indices, color in [
            (left_eye_indices, (255, 255, 0)),
            (right_eye_indices, (255, 255, 0)),
            (mouth_indices, (0, 255, 255)),
        ]:
            pts = []
            for idx in indices:
                lm = face_landmarks[idx]
                pts.append([int(lm.x * w), int(lm.y * h)])
            pts = np.array(pts, dtype=np.int32)
            cv2.polylines(frame, [pts], False, color, 1, cv2.LINE_AA)

        # Draw iris landmarks
        left_iris_indices = [468, 469, 470, 471, 472]
        right_iris_indices = [473, 474, 475, 476, 477]
        for idx in left_iris_indices + right_iris_indices:
            if idx < len(face_landmarks):
                lm = face_landmarks[idx]
                x = int(lm.x * w)
                y = int(lm.y * h)
                cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)

        return frame

    def release(self):
        """Release MediaPipe resources."""
        if self._landmarker:
            self._landmarker.close()
