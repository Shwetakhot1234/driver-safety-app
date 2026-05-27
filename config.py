"""Configuration for Driver Drowsiness & Distraction Detection System."""

# Camera settings
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Eye Aspect Ratio (EAR) thresholds
EAR_THRESHOLD = 0.25
CONSECUTIVE_FRAMES_DROWSY = 15

# Mouth Aspect Ratio (MAR) thresholds
# Multi-point MAR: normal ~0.05-0.15, talking ~0.2-0.35, yawning ~0.4+
MAR_THRESHOLD = 0.5
CONSECUTIVE_FRAMES_YAWN = 8

# Head direction ratio thresholds (normalized ratios)
# These represent how far the nose has shifted from the face center
# 0.0 = looking straight, higher = looking away
# Typical looking-at-camera: yaw ~0.05-0.15, pitch ~0.05-0.15
# Only trigger when clearly NOT looking at camera
HEAD_YAW_RATIO_THRESHOLD = 0.22    # Horizontal head turn
HEAD_PITCH_RATIO_THRESHOLD = 0.30  # Vertical head tilt (looking up/down)
CONSECUTIVE_FRAMES_DISTRACTED = 8

# Phone usage detection thresholds
# Looking down with eyes open = likely using phone
# pitch_ratio: negative when looking down
# gaze_vertical: negative when eyes looking down
PHONE_PITCH_RATIO_THRESHOLD = -0.25   # Head tilted down
PHONE_GAZE_VERTICAL_THRESHOLD = -0.10  # Eyes looking down
CONSECUTIVE_FRAMES_PHONE = 6

# Gaze deviation threshold (normalized ratio - iris offset from eye center)
# ~0.0 when looking at camera, higher when looking away
# Typical looking-at-camera value: ~0.0-0.06, looking away: ~0.08+
GAZE_RATIO_THRESHOLD = 0.08

# Alert settings
ALERT_COOLDOWN = 3.0         # seconds between repeated alerts
ALERT_BEEP_FREQUENCY_DROWSY = 800   # Hz
ALERT_BEEP_FREQUENCY_DISTRACTED = 600  # Hz
ALERT_BEEP_DURATION = 500     # milliseconds

# Display settings
SHOW_LANDMARKS = True
SHOW_METRICS = True
