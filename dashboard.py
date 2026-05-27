"""Main Detection Dashboard Screen.

Contains the live camera feed with OpenCV processing and the
real-time metrics dashboard below it. This is the core monitoring UI.
"""

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.gridlayout import MDGridLayout

from ui.widgets import (
    RiskIndicator, MetricCard, StatusBadge, AlertOverlay, EmergencyBanner,
)


DASHBOARD_KV = """
<DashboardScreen>:
    orientation: 'vertical'

    # --- Full-screen camera feed as background ---
    FloatLayout:

        Image:
            id: camera_image
            allow_stretch: True
            keep_ratio: True
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            size_hint: 1, 1

        # Semi-transparent dark overlay at top for risk/status
        MDCard:
            pos_hint: {'center_x': 0.5, 'top': 0.98}
            size_hint: 0.95, None
            height: dp(72)
            md_bg_color: [0.04, 0.04, 0.06, 0.85]
            radius: [dp(10)]
            padding: dp(6)
            spacing: dp(2)

            BoxLayout:
                orientation: 'vertical'

                RiskIndicator:
                    id: risk_indicator
                    size_hint_y: None
                    height: dp(40)

                StatusBadge:
                    id: status_badge
                    size_hint_y: None
                    height: dp(24)

        # Semi-transparent dark overlay at bottom for metrics
        MDCard:
            pos_hint: {'center_x': 0.5, 'y': 0.04}
            size_hint: 0.95, None
            height: dp(155)
            md_bg_color: [0.04, 0.04, 0.06, 0.88]
            radius: [dp(10)]
            padding: dp(6)
            spacing: dp(3)

            BoxLayout:
                orientation: 'vertical'

                MDGridLayout:
                    cols: 2
                    spacing: dp(4)
                    adaptive_height: True
                    size_hint_y: None
                    height: dp(90)

                    MetricCard:
                        id: ear_card
                        metric_name: "EAR"
                        metric_value: "0.00"

                    MetricCard:
                        id: mar_card
                        metric_name: "MAR"
                        metric_value: "0.00"

                    MetricCard:
                        id: attention_card
                        metric_name: "ATTENTION"
                        metric_value: "100"

                    MetricCard:
                        id: fatigue_card
                        metric_name: "FATIGUE"
                        metric_value: "0"

                MDLabel:
                    id: timer_label
                    text: "Smart Timer: Normal"
                    font_style: 'Caption'
                    halign: 'center'
                    theme_text_color: 'Custom'
                    text_color: [0.70, 0.70, 0.75, 1.0]
                    size_hint_y: None
                    height: dp(16)

                MDRaisedButton:
                    id: stop_button
                    text: "STOP MONITORING"
                    md_bg_color: [0.90, 0.20, 0.20, 1.0]
                    size_hint_y: None
                    height: dp(36)
                    on_release: root.stop_monitoring()

        AlertOverlay:
            id: alert_overlay
            pos_hint: {'center_x': 0.5, 'center_y': 0.65}

        EmergencyBanner:
            id: emergency_banner
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}

        MDLabel:
            id: fps_label
            text: "FPS: --"
            font_style: 'Caption'
            halign: 'right'
            theme_text_color: 'Custom'
            text_color: [0.6, 0.6, 0.6, 0.7]
            size_hint: None, None
            size: dp(70), dp(16)
            pos_hint: {'right': 0.98, 'top': 0.99}

        MDLabel:
            id: no_face_label
            text: ""
            font_style: 'H6'
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: [0.90, 0.20, 0.20, 1.0]
            size_hint: None, None
            size: dp(250), dp(30)
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            opacity: 0
"""


class DashboardScreen(MDScreen):
    """Main detection dashboard with camera feed and metrics."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = None  # Set by main.py

    def update_ui(self, detection_data):
        """Update all dashboard widgets with latest detection data."""
        drowsy = detection_data.get('drowsiness_result', {})
        distract = detection_data.get('distraction_result', {})
        fatigue = detection_data.get('fatigue_result', {})
        timer = detection_data.get('smart_timer_result', {})
        emergency = detection_data.get('emergency_result', {})
        fps = detection_data.get('fps', 0)
        has_face = detection_data.get('has_face', True)
        frame_texture = detection_data.get('frame_texture')

        # Camera feed
        if frame_texture:
            self.ids.camera_image.texture = frame_texture

        # FPS
        self.ids.fps_label.text = f"FPS: {fps:.0f}"

        # No face warning
        if not has_face:
            self.ids.no_face_label.text = "NO FACE DETECTED"
            self.ids.no_face_label.opacity = 1
        else:
            self.ids.no_face_label.opacity = 0

        # Risk Indicator
        risk_level = fatigue.get('risk_level', 'SAFE')
        fatigue_score = fatigue.get('fatigue_score', 0)
        self.ids.risk_indicator.update_risk(risk_level, fatigue_score)

        # Status Badge
        status_key = self._determine_status(drowsy, distract, emergency)
        self.ids.status_badge.update_status(status_key[0], color=status_key[1])

        # Metric Cards
        ear = drowsy.get('ear', 0)
        mar = drowsy.get('mar', 0)
        attention = fatigue.get('attention_score', 100)
        fatigue_val = fatigue.get('fatigue_score', 0)

        self.ids.ear_card.update_metric(
            "EAR", ear, 0.45,
            color=[0.18, 0.80, 0.44, 1.0] if ear >= 0.25 else [0.90, 0.20, 0.20, 1.0]
        )
        self.ids.mar_card.update_metric(
            "MAR", mar, 1.0,
            color=[0.18, 0.80, 0.44, 1.0] if mar < 0.5 else [0.90, 0.20, 0.20, 1.0]
        )
        self.ids.attention_card.update_metric(
            "ATTENTION", attention, 100,
            color=[0.40, 0.85, 0.60, 1.0]
        )
        self.ids.fatigue_card.update_metric(
            "FATIGUE", fatigue_val, 100,
            color=[0.90, 0.30, 0.60, 1.0]
        )

        # Alert Overlay
        alert_type, alert_msg = self._get_highest_alert(drowsy, distract)
        if alert_type and has_face:
            self.ids.alert_overlay.show_alert(
                alert_type.upper() + " DETECTED", alert_msg,
                color=self._status_color(alert_type)
            )
        else:
            self.ids.alert_overlay.hide_alert()

        # Emergency Banner
        if emergency.get('is_emergency', False):
            self.ids.emergency_banner.show_emergency(
                message=emergency.get('message', 'Critical fatigue detected!'),
                location=detection_data.get('gps_link', '')
            )
        else:
            self.ids.emergency_banner.dismiss()

        # Smart Timer Label
        level = timer.get('current_level', 0)
        level_name = timer.get('level_name', 'Normal')
        self.ids.timer_label.text = f"Smart Timer: Level {level} ({level_name})"
        if level >= 3:
            self.ids.timer_label.color = [0.80, 0.05, 0.05, 1.0]
        elif level >= 1:
            self.ids.timer_label.color = [0.95, 0.61, 0.07, 1.0]
        else:
            self.ids.timer_label.color = [0.70, 0.70, 0.75, 1.0]

    def _determine_status(self, drowsy, distract, emergency):
        if emergency.get('is_emergency', False):
            return "EMERGENCY", [0.80, 0.05, 0.05, 1.0]
        if drowsy.get('is_drowsy', False):
            return "DROWSINESS ALERT", [0.90, 0.20, 0.20, 1.0]
        if distract.get('is_phone_usage', False):
            return "PHONE USAGE", [0.90, 0.20, 0.20, 1.0]
        if drowsy.get('is_yawning', False):
            return "YAWN DETECTED", [0.95, 0.61, 0.07, 1.0]
        if distract.get('is_distracted', False):
            return "DISTRACTED", [0.95, 0.61, 0.07, 1.0]
        if drowsy.get('eyes_closed', False):
            return "EYES CLOSING", [0.95, 0.61, 0.07, 1.0]
        return "NORMAL", [0.18, 0.80, 0.44, 1.0]

    def _get_highest_alert(self, drowsy, distract):
        if drowsy.get('is_drowsy', False):
            return 'drowsy', "Wake up driver!"
        if distract.get('is_phone_usage', False):
            return 'phone', "Put down your phone!"
        if drowsy.get('is_yawning', False):
            return 'yawning', "Feeling sleepy? Take a break"
        if distract.get('is_distracted', False):
            return 'distracted', "Focus on driving!"
        if drowsy.get('eyes_closed', False):
            return 'eyes_closed', "Eyes closing! Stay alert"
        return None, None

    @staticmethod
    def _status_color(key):
        colors = {
            'drowsy': [0.90, 0.20, 0.20, 1.0],
            'phone': [0.90, 0.20, 0.20, 1.0],
            'yawning': [0.95, 0.61, 0.07, 1.0],
            'distracted': [0.95, 0.61, 0.07, 1.0],
            'eyes_closed': [0.95, 0.61, 0.07, 1.0],
        }
        return colors.get(key, [0.90, 0.20, 0.20, 1.0])

    def stop_monitoring(self):
        if self._app:
            self._app.stop_monitoring()


Builder.load_string(DASHBOARD_KV)
