"""Utility functions and MediaPipe landmark index mappings."""

import numpy as np


# ---------------------------------------------------------------------------
# MediaPipe Face Mesh landmark indices
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png  # noqa: E501
# ---------------------------------------------------------------------------

# Left eye landmarks (6 points for EAR)
LEFT_EYE = [33, 160, 158, 133, 153, 144]

# Right eye landmarks (6 points for EAR)
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# Mouth landmarks for MAR (yawn detection)
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
MOUTH_LEFT = 61
MOUTH_RIGHT = 291
MOUTH_UPPER_LEFT = 82
MOUTH_UPPER_RIGHT = 312
MOUTH_LOWER_LEFT = 87
MOUTH_LOWER_RIGHT = 317

# All mouth landmarks for comprehensive MAR calculation
MOUTH_ALL = [MOUTH_TOP, MOUTH_BOTTOM, MOUTH_LEFT, MOUTH_RIGHT,
             MOUTH_UPPER_LEFT, MOUTH_UPPER_RIGHT, MOUTH_LOWER_LEFT, MOUTH_LOWER_RIGHT]

# Head pose / direction estimation landmarks
NOSE_TIP = 1
CHIN = 152
LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263
LEFT_MOUTH_CORNER = 61
RIGHT_MOUTH_CORNER = 291
FOREHEAD_GLABELLA = 168  # Point between the eyebrows

HEAD_POSE_LANDMARKS = [
    NOSE_TIP,
    CHIN,
    LEFT_EYE_OUTER,
    RIGHT_EYE_OUTER,
    LEFT_MOUTH_CORNER,
    RIGHT_MOUTH_CORNER,
]

# Iris landmarks (MediaPipe provides iris with refine_landmarks)
LEFT_IRIS = [468, 469, 470, 471, 472]   # center + 4 boundary points
RIGHT_IRIS = [473, 474, 475, 476, 477]  # center + 4 boundary points

# Left eye boundary for gaze (outer corner, top, bottom, inner corner)
LEFT_EYE_BOUNDARY = [33, 160, 158, 133]
# Right eye boundary for gaze (outer corner, top, bottom, inner corner)
RIGHT_EYE_BOUNDARY = [362, 385, 387, 263]


def get_landmark_coords(landmarks, indices, frame_w, frame_h):
    """Extract (x, y) pixel coordinates for given landmark indices.

    Args:
        landmarks: List of NormalizedLandmark objects from MediaPipe Tasks API.
            Each landmark has .x, .y, .z attributes (normalized 0-1).
        indices: List of landmark indices.
        frame_w: Frame width in pixels.
        frame_h: Frame height in pixels.

    Returns:
        numpy array of shape (N, 2) with pixel coordinates.
    """
    points = []
    for idx in indices:
        lm = landmarks[idx]
        points.append([lm.x * frame_w, lm.y * frame_h])
    return np.array(points, dtype=np.float64)


def euclidean_distance(p1, p2):
    """Compute Euclidean distance between two 2D points."""
    return np.linalg.norm(np.array(p1) - np.array(p2))
