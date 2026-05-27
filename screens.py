"""All App Screens for the driver safety monitoring app.

Screens:
- SplashScreen: App logo + loading
- HomeScreen: Start monitoring, settings, session summary
- MonitoringScreen: Live detection dashboard
- SettingsScreen: Emergency contacts, sensitivity, voice on/off
- SessionSummaryScreen: Post-session analytics + report export
"""

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

import config
from ui.dashboard import DashboardScreen


# ---------------------------------------------------------------------------
# Splash Screen
# ---------------------------------------------------------------------------
SPLASH_KV = """
<SplashScreen>:
    orientation: 'vertical'
    md_bg_color: [0.06, 0.06, 0.08, 1.0]

    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(40)
        spacing: dp(20)

        MDLabel:
            text: "Driver Safety"
            font_style: 'H3'
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: [0.18, 0.80, 0.44, 1.0]

        MDLabel:
            text: "AI-Based Predictive Monitoring"
            font_style: 'Subtitle1'
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: [0.70, 0.70, 0.75, 1.0]

        MDLabel:
            text: "Loading models..."
            font_style: 'Body2'
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: [0.70, 0.70, 0.75, 1.0]
            id: loading_label

        MDProgressBar:
            id: progress_bar
            value: 0
            color: [0.18, 0.80, 0.44, 1.0]
"""


class SplashScreen(MDScreen):
    """Splash screen shown during model loading."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_progress(self, value, label_text=""):
        if 'progress_bar' in self.ids:
            self.ids.progress_bar.value = value
        if label_text and 'loading_label' in self.ids:
            self.ids.loading_label.text = label_text


# ---------------------------------------------------------------------------
# Home Screen
# ---------------------------------------------------------------------------
HOME_KV = """
<HomeScreen>:
    orientation: 'vertical'
    md_bg_color: [0.06, 0.06, 0.08, 1.0]

    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(16)

        MDLabel:
            text: "Driver Safety Monitor"
            font_style: 'H4'
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: [0.18, 0.80, 0.44, 1.0]
            size_hint_y: None
            height: dp(50)

        MDLabel:
            text: "AI-Powered Predictive Driver Safety\\nand Emergency Alert System"
            font_style: 'Body1'
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: [0.70, 0.70, 0.75, 1.0]
            size_hint_y: None
            height: dp(40)

        MDBoxLayout:
            size_hint_y: None
            height: dp(30)

        MDRaisedButton:
            text: "START MONITORING"
            font_style: 'Button'
            size_hint: 0.7, None
            height: dp(56)
            pos_hint: {'center_x': 0.5}
            md_bg_color: [0.18, 0.80, 0.44, 1.0]
            on_release: root.start_monitoring()

        MDFlatButton:
            text: "Settings"
            size_hint: 0.5, None
            height: dp(44)
            pos_hint: {'center_x': 0.5}
            theme_text_color: 'Custom'
            text_color: [0.20, 0.60, 0.95, 1.0]
            on_release: root.open_settings()

        MDFlatButton:
            text: "Session Summary"
            size_hint: 0.5, None
            height: dp(44)
            pos_hint: {'center_x': 0.5}
            theme_text_color: 'Custom'
            text_color: [0.20, 0.60, 0.95, 1.0]
            on_release: root.open_session_summary()

        MDBoxLayout:
            size_hint_y: None
            height: dp(20)

        MDCard:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(8)
            size_hint_y: None
            height: dp(120)
            md_bg_color: [0.14, 0.14, 0.18, 1.0]
            radius: [dp(12)]

            MDLabel:
                text: "System Features"
                font_style: 'Subtitle1'
                theme_text_color: 'Custom'
                text_color: [0.18, 0.80, 0.44, 1.0]

            MDLabel:
                text: "- Drowsiness & Yawning Detection\\n- Distraction & Phone Usage Alert\\n- Predictive Fatigue Analysis\\n- Emergency GPS + SMS Alerts"
                font_style: 'Caption'
                theme_text_color: 'Custom'
                text_color: [0.70, 0.70, 0.75, 1.0]
"""


class HomeScreen(MDScreen):
    """Home screen with start monitoring and navigation buttons."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = None

    def start_monitoring(self):
        if self._app:
            self._app.start_monitoring()

    def open_settings(self):
        if self._app:
            self._app.show_screen('settings')

    def open_session_summary(self):
        if self._app:
            self._app.show_screen('summary')


# ---------------------------------------------------------------------------
# Settings Screen
# ---------------------------------------------------------------------------
SETTINGS_KV = """
<SettingsScreen>:
    orientation: 'vertical'
    md_bg_color: [0.06, 0.06, 0.08, 1.0]

    MDTopAppBar:
        title: "Settings"
        left_action_items: [['arrow-left', lambda x: root.go_back()]]
        md_bg_color: [0.14, 0.14, 0.18, 1.0]
        specific_text_color: [1.0, 1.0, 1.0, 1.0]

    MDScrollView:
        MDList:
            id: settings_list

            TwoLineListItem:
                text: "Emergency Contacts"
                secondary_text: "Add phone numbers for emergency SMS"
                on_release: root.edit_contacts()

            TwoLineListItem:
                text: "Driver Name"
                secondary_text: "Name used in emergency messages"
                on_release: root.edit_driver_name()

            TwoLineListItem:
                text: "Voice Alerts"
                secondary_text: "Enable/disable voice alerts"
                on_release: root.toggle_voice()

            TwoLineListItem:
                text: "Detection Sensitivity"
                secondary_text: "Adjust EAR/MAR thresholds"
                on_release: root.edit_sensitivity()

            TwoLineListItem:
                text: "Smart Timer Delays"
                secondary_text: "Configure escalation timing"
                on_release: root.edit_timer_delays()

            TwoLineListItem:
                text: "GPS Tracking"
                secondary_text: "Enable/disable GPS for emergencies"
                on_release: root.toggle_gps()
"""


class SettingsScreen(MDScreen):
    """Settings screen for configuration."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = None
        self._dialog = None

    def go_back(self):
        if self._app:
            self._app.show_screen('home')

    def edit_contacts(self):
        self._show_input_dialog(
            "Emergency Contacts",
            "Enter phone numbers (comma-separated):",
            ", ".join(config.EMERGENCY_CONTACTS) if config.EMERGENCY_CONTACTS else "",
            self._save_contacts
        )

    def edit_driver_name(self):
        self._show_input_dialog(
            "Driver Name", "Enter driver name:",
            config.DRIVER_NAME, self._save_driver_name
        )

    def toggle_voice(self):
        config.VOICE_ENABLED = not config.VOICE_ENABLED

    def edit_sensitivity(self):
        self._show_input_dialog(
            "EAR Threshold",
            f"Current: {config.EAR_THRESHOLD}. Enter new value (0.1-0.4):",
            str(config.EAR_THRESHOLD), self._save_ear_threshold
        )

    def edit_timer_delays(self):
        self._show_input_dialog(
            "Level 2 Delay (seconds)",
            f"Current: {config.SMART_TIMER_LEVEL2_DELAY}s. Enter new value:",
            str(config.SMART_TIMER_LEVEL2_DELAY), self._save_level2_delay
        )

    def toggle_gps(self):
        pass

    def _show_input_dialog(self, title, text, default_value, callback):
        if self._dialog:
            self._dialog.dismiss()
        text_field = MDTextField(text=default_value, mode="rectangle")
        self._dialog = MDDialog(
            title=title, text=text, type="custom",
            content_cls=text_field,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self._dialog.dismiss()),
                MDRaisedButton(text="SAVE", on_release=lambda x: self._save_dialog(callback, text_field)),
            ],
        )
        self._dialog.open()

    def _save_dialog(self, callback, text_field):
        callback(text_field.text)
        if self._dialog:
            self._dialog.dismiss()

    def _save_contacts(self, value):
        contacts = [c.strip() for c in value.split(',') if c.strip()]
        config.EMERGENCY_CONTACTS = contacts

    def _save_driver_name(self, value):
        config.DRIVER_NAME = value.strip() or "Driver"

    def _save_ear_threshold(self, value):
        try:
            val = float(value)
            if 0.1 <= val <= 0.4:
                config.EAR_THRESHOLD = val
        except ValueError:
            pass

    def _save_level2_delay(self, value):
        try:
            val = int(value)
            if val > 0:
                config.SMART_TIMER_LEVEL2_DELAY = val
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Session Summary Screen
# ---------------------------------------------------------------------------
SUMMARY_KV = """
<SessionSummaryScreen>:
    orientation: 'vertical'
    md_bg_color: [0.06, 0.06, 0.08, 1.0]

    MDTopAppBar:
        title: "Session Summary"
        left_action_items: [['arrow-left', lambda x: root.go_back()]]
        md_bg_color: [0.14, 0.14, 0.18, 1.0]
        specific_text_color: [1.0, 1.0, 1.0, 1.0]

    MDScrollView:
        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(16)
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height

            MDCard:
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(8)
                size_hint_y: None
                height: dp(200)
                md_bg_color: [0.14, 0.14, 0.18, 1.0]
                radius: [dp(12)]

                MDLabel:
                    text: "Session Statistics"
                    font_style: 'H6'
                    theme_text_color: 'Custom'
                    text_color: [0.18, 0.80, 0.44, 1.0]

                MDLabel:
                    id: stats_label
                    text: "No session data"
                    font_style: 'Body2'
                    theme_text_color: 'Custom'
                    text_color: [0.70, 0.70, 0.75, 1.0]

            MDCard:
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(8)
                size_hint_y: None
                height: dp(180)
                md_bg_color: [0.14, 0.14, 0.18, 1.0]
                radius: [dp(12)]

                MDLabel:
                    text: "Export Report"
                    font_style: 'H6'
                    theme_text_color: 'Custom'
                    text_color: [0.18, 0.80, 0.44, 1.0]

                MDRaisedButton:
                    text: "Export as TXT"
                    size_hint_x: 0.8
                    pos_hint: {'center_x': 0.5}
                    md_bg_color: [0.20, 0.60, 0.95, 1.0]
                    on_release: root.export_txt()

                MDRaisedButton:
                    text: "Export as CSV"
                    size_hint_x: 0.8
                    pos_hint: {'center_x': 0.5}
                    md_bg_color: [0.20, 0.60, 0.95, 1.0]
                    on_release: root.export_csv()

                MDRaisedButton:
                    text: "Export as PDF"
                    size_hint_x: 0.8
                    pos_hint: {'center_x': 0.5}
                    md_bg_color: [0.20, 0.60, 0.95, 1.0]
                    on_release: root.export_pdf()

            MDRaisedButton:
                text: "START NEW SESSION"
                size_hint: 0.7, None
                height: dp(50)
                pos_hint: {'center_x': 0.5}
                md_bg_color: [0.18, 0.80, 0.44, 1.0]
                on_release: root.new_session()
"""


class SessionSummaryScreen(MDScreen):
    """Post-session analytics and report export screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = None
        self._session_summary = None
        self._event_log = None

    def update_summary(self, session_summary, event_log):
        self._session_summary = session_summary
        self._event_log = event_log

        if session_summary and 'stats_label' in self.ids:
            duration = session_summary.get('session_duration', 0)
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)

            text = (
                f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}\n\n"
                f"Total Yawns: {session_summary.get('total_yawns', 0)}\n"
                f"Drowsiness Events: {session_summary.get('drowsiness_events', 0)}\n"
                f"Phone Usage: {session_summary.get('phone_usage_events', 0)}\n"
                f"Distractions: {session_summary.get('distraction_count', 0)}\n\n"
                f"Max Fatigue: {session_summary.get('max_fatigue_score', 0):.1f}/100 "
                f"({session_summary.get('max_fatigue_level', 'N/A')})\n"
                f"Avg EAR: {session_summary.get('average_ear', 0):.3f}\n"
                f"Avg MAR: {session_summary.get('average_mar', 0):.3f}"
            )
            self.ids.stats_label.text = text

    def go_back(self):
        if self._app:
            self._app.show_screen('home')

    def export_txt(self):
        if self._app and self._session_summary:
            self._app.export_report('txt', self._session_summary, self._event_log)

    def export_csv(self):
        if self._app and self._session_summary:
            self._app.export_report('csv', self._session_summary, self._event_log)

    def export_pdf(self):
        if self._app and self._session_summary:
            self._app.export_report('pdf', self._session_summary, self._event_log)

    def new_session(self):
        if self._app:
            self._app.start_monitoring()


# Load all KV definitions
Builder.load_string(SPLASH_KV)
Builder.load_string(HOME_KV)
Builder.load_string(SETTINGS_KV)
Builder.load_string(SUMMARY_KV)
