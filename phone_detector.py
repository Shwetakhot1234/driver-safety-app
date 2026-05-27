"""Phone object detection using MediaPipe ObjectDetector.

Uses MediaPipe's EfficientDet-Lite0 model to detect mobile phones
in the camera frame. The COCO dataset includes "cell phone" as a
detectable class, which we filter for specifically.

Implements multi-criteria validation to reduce false positives:
1. ML confidence threshold (high)
2. Aspect ratio check (phones are tall/narrow)
3. Size check (must be reasonable phone size)
4. Persistence check (must be detected for N consecutive frames)
"""

import time
import cv2
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[WARNING] MediaPipe not available. Phone detection disabled.")

import config

# COCO class name for cell phone
PHONE_LABEL = "cell phone"

# Phone size criteria (as fraction of frame area):
# - Too small = likely false positive (noise, distant object)
# - Too large = probably not a phone held in hand
PHONE_MIN_AREA_RATIO = 0.002   # At least 0.2% of frame area (small/distant phone)
PHONE_MAX_AREA_RATIO = 0.35    # At most 35% of frame area

# Persistence: phone must be detected in N consecutive checks
# before we confirm it (prevents flickering false positives)
PHONE_PERSIST_FRAMES = 2


class PhoneDetector:
    """Detects mobile phones in video frames with multi-criteria validation.

    Validation pipeline:
    1. MediaPipe EfficientDet-Lite0 detects "cell phone" objects
    2. Filter by confidence threshold (0.55+)
    3. Validate bounding box size relative to frame
    4. Require N consecutive detections before confirming
    5. Combined with driver head-down check (in distraction.py)
       for final "phone usage" determination
    """

    def __init__(self, confidence=0.55):
        """Initialize MediaPipe ObjectDetector for phone detection.

        Args:
            confidence: Minimum confidence threshold for detection.
                        0.55 = balanced between accuracy and recall.
        """
        self._model = None
        self._confidence = confidence
        self._phone_detected = False
        self._phone_box = None
        self._phone_confidence = 0.0
        self._detection_streak = 0     # Consecutive frames with valid phone detection
        self._confirmed_phone = False   # Only True after persistence check passes
        self._confirmed_box = None      # Bounding box of confirmed phone
        self._load_model()

    def _load_model(self):
        """Load MediaPipe EfficientDet-Lite0 model."""
        try:
            import os
            model_path = config.PHONE_MODEL_PATH

            if not model_path or not os.path.exists(model_path):
                print(f"[WARNING] Phone detection model not found: {model_path}")
                print("[WARNING] Phone object detection disabled.")
                return

            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.ObjectDetectorOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                score_threshold=self._confidence,
                category_allowlist=[PHONE_LABEL],
            )
            self._model = vision.ObjectDetector.create_from_options(options)
            print("[INFO] MediaPipe phone detector ready (EfficientDet-Lite0).")

        except Exception as e:
            print(f"[WARNING] Could not load phone detector model: {e}")
            print("[WARNING] Phone object detection disabled.")
            self._model = None

    def _validate_phone_shape(self, bbox, frame_w, frame_h):
        """Validate that a detected object has phone-like size.

        Checks size only (aspect ratio is unreliable since phones
        can be at any angle/orientation when held).

        Args:
            bbox: Bounding box tuple (x1, y1, x2, y2).
            frame_w: Frame width.
            frame_h: Frame height.

        Returns:
            True if the size is reasonable for a phone.
        """
        x1, y1, x2, y2 = bbox
        box_w = x2 - x1
        box_h = y2 - y1

        if box_w <= 0 or box_h <= 0:
            return False

        # Check size relative to frame
        frame_area = frame_w * frame_h
        box_area = box_w * box_h
        area_ratio = box_area / frame_area if frame_area > 0 else 0

        if area_ratio < PHONE_MIN_AREA_RATIO or area_ratio > PHONE_MAX_AREA_RATIO:
            return False

        return True

    def detect(self, frame):
        """Run phone detection on a single frame with full validation.

        Pipeline:
        1. Run ML object detection
        2. Filter by confidence threshold
        3. Validate shape/size of detection
        4. Apply persistence check (must detect N times)

        Args:
            frame: BGR image (numpy array).

        Returns:
            dict with:
                'phone_detected': bool - True only after all checks pass
                'phone_box': tuple (x1,y1,x2,y2) or None
                'confidence': float
        """
        if self._model is None:
            self._phone_detected = False
            self._phone_box = None
            self._confirmed_phone = False
            self._detection_streak = 0
            return {'phone_detected': False, 'phone_box': None, 'confidence': 0.0}

        frame_h, frame_w = frame.shape[:2]

        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            results = self._model.detect(mp_image)

            raw_detected = False
            raw_box = None
            raw_confidence = 0.0

            if results.detections:
                # Find the best phone detection that passes ALL validation
                best_det = None
                best_score = 0.0
                best_box = None

                for det in results.detections:
                    for category in det.categories:
                        if category.category_name == PHONE_LABEL and category.score >= self._confidence:
                            bbox = det.bounding_box
                            box = (int(bbox.origin_x), int(bbox.origin_y),
                                   int(bbox.origin_x + bbox.width),
                                   int(bbox.origin_y + bbox.height))

                            # Validate shape and size
                            if self._validate_phone_shape(box, frame_w, frame_h):
                                if category.score > best_score:
                                    best_score = category.score
                                    best_det = det
                                    best_box = box

                if best_det is not None:
                    raw_detected = True
                    raw_box = best_box
                    raw_confidence = best_score

            # --- Persistence check ---
            if raw_detected:
                self._detection_streak += 1
                self._phone_confidence = raw_confidence
                self._phone_box = raw_box
            else:
                self._detection_streak = max(0, self._detection_streak - 2)
                if self._detection_streak == 0:
                    self._phone_confidence = 0.0
                    self._phone_box = None

            # Confirm phone only after N consecutive valid detections
            if self._detection_streak >= PHONE_PERSIST_FRAMES:
                self._confirmed_phone = True
                self._confirmed_box = self._phone_box
            else:
                self._confirmed_phone = False

            # If we had a confirmed phone but lost it briefly, keep it
            # for 2 more checks before fully clearing (hysteresis)
            if not raw_detected and self._confirmed_phone:
                if self._detection_streak <= 0:
                    self._confirmed_phone = False
                    self._confirmed_box = None

            self._phone_detected = self._confirmed_phone

            return {
                'phone_detected': self._confirmed_phone,
                'phone_box': self._confirmed_box if self._confirmed_phone else None,
                'confidence': self._phone_confidence if self._confirmed_phone else 0.0,
            }

        except Exception:
            self._phone_detected = False
            self._phone_box = None
            self._phone_confidence = 0.0
            self._detection_streak = max(0, self._detection_streak - 1)
            return {'phone_detected': False, 'phone_box': None, 'confidence': 0.0}

    def draw_phone_box(self, frame, phone_result):
        """Draw bounding box around confirmed phone (no percentage label).

        Args:
            frame: BGR image.
            phone_result: dict from detect().

        Returns:
            Frame with phone box drawn.
        """
        if phone_result.get('phone_detected') and phone_result.get('phone_box'):
            x1, y1, x2, y2 = phone_result['phone_box']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.rectangle(frame, (x1, y1 - 22), (x1 + 70, y1), (0, 0, 255), -1)
            cv2.putText(frame, "PHONE", (x1 + 5, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return frame
