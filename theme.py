"""Dark Theme configuration for KivyMD UI.

Defines the color palette, font sizes, spacing, and style constants
used throughout the mobile app's futuristic dark-mode interface.
"""

# ---------------------------------------------------------------------------
# Color palette (RGBA floats 0-1 for Kivy compatibility)
# ---------------------------------------------------------------------------

# Background colors
BG_PRIMARY = [0.06, 0.06, 0.08, 1.0]         # Deep dark background
BG_SECONDARY = [0.10, 0.10, 0.14, 1.0]        # Slightly lighter panels
BG_CARD = [0.14, 0.14, 0.18, 1.0]             # Card background
BG_CARD_HOVER = [0.18, 0.18, 0.22, 1.0]       # Card on hover/press

# Status/Risk colors
COLOR_SAFE = [0.18, 0.80, 0.44, 1.0]           # Green - SAFE
COLOR_WARNING = [0.95, 0.61, 0.07, 1.0]        # Orange - WARNING
COLOR_DANGER = [0.90, 0.20, 0.20, 1.0]         # Red - DANGEROUS
COLOR_CRITICAL = [0.80, 0.05, 0.05, 1.0]       # Deep red - EMERGENCY

# Text colors
TEXT_PRIMARY = [1.0, 1.0, 1.0, 1.0]            # White - primary text
TEXT_SECONDARY = [0.70, 0.70, 0.75, 1.0]       # Gray - secondary text
TEXT_ACCENT = [0.30, 0.70, 0.95, 1.0]          # Light blue - accent
TEXT_MUTED = [0.50, 0.50, 0.55, 1.0]           # Dark gray - muted text

# Metric colors
COLOR_EAR = [0.20, 0.75, 0.90, 1.0]            # Cyan - EAR metric
COLOR_MAR = [0.95, 0.55, 0.20, 1.0]            # Orange - MAR metric
COLOR_ATTENTION = [0.40, 0.85, 0.60, 1.0]      # Light green - attention
COLOR_FATIGUE = [0.90, 0.30, 0.60, 1.0]        # Pink - fatigue

# UI accent colors
ACCENT_PRIMARY = [0.20, 0.60, 0.95, 1.0]       # Blue - primary accent
ACCENT_SECONDARY = [0.60, 0.30, 0.90, 1.0]     # Purple - secondary accent

# Overlay colors
OVERLAY_DARK = [0.0, 0.0, 0.0, 0.6]            # Semi-transparent black
OVERLAY_ALERT = [0.8, 0.1, 0.1, 0.4]           # Red alert overlay
OVERLAY_WARNING = [0.9, 0.6, 0.0, 0.3]         # Orange warning overlay

# ---------------------------------------------------------------------------
# Risk level color mapping
# ---------------------------------------------------------------------------
RISK_COLORS = {
    "SAFE": COLOR_SAFE,
    "WARNING": COLOR_WARNING,
    "DANGEROUS": COLOR_DANGER,
}

# ---------------------------------------------------------------------------
# Font sizes (sp - scale-independent pixels)
# ---------------------------------------------------------------------------
FONT_SIZE_H1 = "24sp"
FONT_SIZE_H2 = "20sp"
FONT_SIZE_H3 = "16sp"
FONT_SIZE_BODY = "14sp"
FONT_SIZE_SMALL = "12sp"
FONT_SIZE_TINY = "10sp"
FONT_SIZE_METRIC_VALUE = "28sp"
FONT_SIZE_METRIC_LABEL = "11sp"
FONT_SIZE_STATUS = "18sp"

# ---------------------------------------------------------------------------
# Spacing (dp - density-independent pixels)
# ---------------------------------------------------------------------------
SPACING_XS = "4dp"
SPACING_SM = "8dp"
SPACING_MD = "12dp"
SPACING_LG = "16dp"
SPACING_XL = "24dp"
SPACING_XXL = "32dp"

# ---------------------------------------------------------------------------
# Card dimensions
# ---------------------------------------------------------------------------
CARD_RADIUS = "12dp"
CARD_ELEVATION = "2dp"
CARD_PADDING = "12dp"

# ---------------------------------------------------------------------------
# Status text mapping
# ---------------------------------------------------------------------------
STATUS_TEXT = {
    'normal': "NORMAL",
    'drowsy': "DROWSINESS ALERT",
    'yawning': "YAWN DETECTED",
    'distracted': "DISTRACTED",
    'phone': "PHONE USAGE",
    'emergency': "EMERGENCY",
}

STATUS_COLORS = {
    'normal': COLOR_SAFE,
    'drowsy': COLOR_DANGER,
    'yawning': COLOR_WARNING,
    'distracted': COLOR_WARNING,
    'phone': COLOR_DANGER,
    'emergency': COLOR_CRITICAL,
}


def get_risk_color(risk_level):
    """Get the color for a risk level string.

    Args:
        risk_level: 'SAFE', 'WARNING', or 'DANGEROUS'.

    Returns:
        RGBA list.
    """
    return RISK_COLORS.get(risk_level, COLOR_SAFE)


def get_status_color(status_key):
    """Get the color for a driver status key.

    Args:
        status_key: 'normal', 'drowsy', 'yawning', etc.

    Returns:
        RGBA list.
    """
    return STATUS_COLORS.get(status_key, COLOR_SAFE)
