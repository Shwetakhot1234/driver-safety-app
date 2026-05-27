"""Custom KivyMD Widgets for the driver safety monitoring app.

Includes:
- RiskIndicator: Animated color-coded risk level card
- MetricCard: Displays metric name + value + progress bar
- StatusBadge: Driver status display with color indicator
- FatigueGauge: Circular fatigue level indicator
- AlertOverlay: Animated warning panel
- EmergencyBanner: Full-screen emergency status display
"""

from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.progressbar import ProgressBar
from kivy.metrics import dp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar

from ui.theme import (
    COLOR_SAFE, COLOR_WARNING, COLOR_DANGER, COLOR_CRITICAL,
    COLOR_EAR, COLOR_MAR, COLOR_ATTENTION, COLOR_FATIGUE,
    BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY,
    RISK_COLORS, get_risk_color,
)


# ---------------------------------------------------------------------------
# KV language definitions for custom widgets
# ---------------------------------------------------------------------------
BUILDER_WIDGETS = """
<RiskIndicator>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(6)
    size_hint_y: None
    height: dp(80)
    md_bg_color: root.bg_color

    MDLabel:
        text: root.risk_level
        font_style: 'H5'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: root.text_color
        size_hint_y: None
        height: dp(32)

    MDLabel:
        text: root.fatigue_text
        font_style: 'Body2'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: [0.7, 0.7, 0.7, 1.0]
        size_hint_y: None
        height: dp(20)

<MetricCard>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(4)
    size_hint_y: None
    height: dp(90)
    md_bg_color: root.bg_color

    MDLabel:
        text: root.metric_name
        font_style: 'Caption'
        halign: 'left'
        theme_text_color: 'Custom'
        text_color: root.label_color
        size_hint_y: None
        height: dp(16)

    MDLabel:
        text: root.metric_value
        font_style: 'H4'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: root.value_color
        size_hint_y: None
        height: dp(36)

    MDProgressBar:
        value: root.progress_value
        color: root.progress_color
        size_hint_y: None
        height: dp(6)

<StatusBadge>:
    orientation: 'horizontal'
    padding: dp(10)
    spacing: dp(8)
    size_hint_y: None
    height: dp(48)
    md_bg_color: root.bg_color

    # Color indicator dot
    MDFloatLayout:
        size_hint_x: None
        width: dp(24)

        MDCard:
            size_hint: None, None
            size: dp(16), dp(16)
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            md_bg_color: root.indicator_color
            radius: [dp(8)]

    MDLabel:
        text: root.status_text
        font_style: 'Subtitle1'
        halign: 'left'
        theme_text_color: 'Custom'
        text_color: root.text_color
        size_hint_y: None
        height: dp(28)

<AlertOverlay>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(8)
    size_hint: None, None
    size: dp(320), dp(120)
    pos_hint: {'center_x': 0.5, 'center_y': 0.7}
    md_bg_color: root.bg_color
    radius: [dp(12)]
    opacity: 0 if not root.visible else 1.0

    MDLabel:
        text: root.alert_title
        font_style: 'H6'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: root.alert_color

    MDLabel:
        text: root.alert_subtitle
        font_style: 'Body2'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: [0.8, 0.8, 0.8, 1.0]

<EmergencyBanner>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(12)
    size_hint: 1, None
    height: dp(200)
    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
    md_bg_color: [0.15, 0.0, 0.0, 0.95]
    radius: [dp(16)]
    opacity: 0 if not root.visible else 1.0

    MDLabel:
        text: "EMERGENCY"
        font_style: 'H3'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: [0.80, 0.05, 0.05, 1.0]

    MDLabel:
        text: root.emergency_message
        font_style: 'Subtitle1'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: [1.0, 0.6, 0.6, 1.0]

    MDLabel:
        text: root.location_text
        font_style: 'Caption'
        halign: 'center'
        theme_text_color: 'Custom'
        text_color: [0.7, 0.7, 0.7, 1.0]

    MDRaisedButton:
        text: "DISMISS"
        md_bg_color: [0.90, 0.20, 0.20, 1.0]
        pos_hint: {'center_x': 0.5}
        on_release: root.dismiss()
"""


class RiskIndicator(MDCard):
    """Animated color-coded risk level indicator card."""
    risk_level = StringProperty("SAFE")
    fatigue_text = StringProperty("Fatigue: 0/100")
    bg_color = ListProperty(BG_CARD)
    text_color = ListProperty(COLOR_SAFE)

    def update_risk(self, risk_level, fatigue_score):
        """Update the risk indicator display.

        Args:
            risk_level: 'SAFE', 'WARNING', or 'DANGEROUS'.
            fatigue_score: Current fatigue score (0-100).
        """
        self.risk_level = risk_level
        self.fatigue_text = f"Fatigue: {float(fatigue_score):.0f}/100"
        self.text_color = get_risk_color(risk_level)


class MetricCard(MDCard):
    """Displays a metric with name, value, and progress bar."""
    metric_name = StringProperty("EAR")
    metric_value = StringProperty("0.00")
    progress_value = NumericProperty(0)
    progress_color = ListProperty(COLOR_EAR)
    label_color = ListProperty(COLOR_EAR)
    value_color = ListProperty(TEXT_PRIMARY)
    bg_color = ListProperty(BG_CARD)

    def update_metric(self, name, value, max_val=1.0, color=None):
        """Update metric display.

        Args:
            name: Metric name (e.g. 'EAR', 'MAR').
            value: Current value.
            max_val: Maximum value for progress bar.
            color: Optional color override.
        """
        self.metric_name = name
        self.metric_value = f"{float(value):.2f}"
        self.progress_value = float(min((value / max_val) * 100, 100)) if max_val > 0 else 0.0
        if color:
            self.progress_color = color
            self.label_color = color


class StatusBadge(MDCard):
    """Driver status display with color indicator dot."""
    status_text = StringProperty("NORMAL")
    indicator_color = ListProperty(COLOR_SAFE)
    text_color = ListProperty(TEXT_PRIMARY)
    bg_color = ListProperty(BG_CARD)

    def update_status(self, text, color=None):
        """Update status display.

        Args:
            text: Status text.
            color: Indicator color.
        """
        self.status_text = text
        if color:
            self.indicator_color = color


class AlertOverlay(MDCard):
    """Animated warning panel that appears over the camera feed."""
    visible = BooleanProperty(False)
    alert_title = StringProperty("ALERT")
    alert_subtitle = StringProperty("")
    alert_color = ListProperty(COLOR_WARNING)
    bg_color = ListProperty([0.15, 0.08, 0.0, 0.9])

    def show_alert(self, title, subtitle, color=None):
        """Show the alert overlay.

        Args:
            title: Alert title text.
            subtitle: Alert subtitle text.
            color: Alert color.
        """
        self.visible = True
        self.alert_title = title
        self.alert_subtitle = subtitle
        if color:
            self.alert_color = color

    def hide_alert(self):
        """Hide the alert overlay."""
        self.visible = False


class EmergencyBanner(MDCard):
    """Full-screen emergency status display."""
    visible = BooleanProperty(False)
    emergency_message = StringProperty("Critical fatigue detected!")
    location_text = StringProperty("")

    def show_emergency(self, message="", location=""):
        """Show emergency banner.

        Args:
            message: Emergency message.
            location: GPS location text.
        """
        self.visible = True
        self.emergency_message = message or "Critical fatigue detected!"
        self.location_text = location

    def dismiss(self):
        """Dismiss the emergency banner."""
        self.visible = False


# Load KV definitions
Builder.load_string(BUILDER_WIDGETS)
