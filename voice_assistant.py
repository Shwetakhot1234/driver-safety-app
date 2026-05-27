"""Voice Assistant for TTS (Text-to-Speech) alerts.

Uses plyer TTS facade for Android-compatible text-to-speech.
Provides voice alerts with cooldown management and priority system.

Priority: emergency > drowsy > phone > distraction > fatigue_warning
"""

import time

import config


class VoiceAssistant:
    """Text-to-speech voice alert system with cooldown and priority."""

    # Priority levels (higher = more important)
    PRIORITY = {
        'emergency': 5,
        'drowsy': 4,
        'phone': 3,
        'distraction': 2,
        'fatigue_warning': 1,
    }

    # Alert type to message mapping
    ALERT_MESSAGES = {
        'drowsy': config.VOICE_MSG_DROWSY,
        'distraction': config.VOICE_MSG_DISTRACTED,
        'phone': config.VOICE_MSG_PHONE,
        'fatigue_warning': config.VOICE_MSG_FATIGUE_WARNING,
        'emergency': config.VOICE_MSG_EMERGENCY,
        'emergency_contact': config.VOICE_MSG_EMERGENCY_CONTACT,
    }

    def __init__(self):
        self._last_spoken_time = {}       # alert_type -> last timestamp
        self._tts_available = False
        self._init_tts()

    def _init_tts(self):
        """Initialize TTS engine via plyer.

        On Android, plyer TTS uses the native TextToSpeech engine.
        On Windows, plyer TTS may not have a backend, so we test it.
        """
        try:
            from plyer import tts
            # Test if TTS actually works by trying to speak
            # On platforms without a TTS backend, this will fail
            try:
                tts.speak("")  # Empty test
                self._tts_available = True
                print("[INFO] Voice assistant ready (plyer TTS).")
            except Exception:
                # TTS facade exists but backend doesn't work (e.g., Windows)
                self._tts_available = False
                print("[INFO] Voice assistant disabled (no TTS backend on this platform).")
        except ImportError:
            print("[WARNING] plyer TTS not available. Voice alerts disabled.")
            self._tts_available = False
        except Exception as e:
            print(f"[WARNING] TTS initialization failed: {e}")
            self._tts_available = False

    def speak(self, alert_type, custom_message=None):
        """Speak an alert message if cooldown allows.

        Args:
            alert_type: One of 'drowsy', 'distraction', 'phone',
                        'fatigue_warning', 'emergency', 'emergency_contact'.
            custom_message: Optional custom message to speak instead of default.

        Returns:
            True if message was spoken, False if suppressed by cooldown.
        """
        if not config.VOICE_ENABLED or not self._tts_available:
            return False

        # Check cooldown
        now = time.time()
        last_time = self._last_spoken_time.get(alert_type, 0.0)
        if now - last_time < config.VOICE_COOLDOWN:
            return False

        # Get message
        message = custom_message or self.ALERT_MESSAGES.get(alert_type, "")

        if not message:
            return False

        try:
            from plyer import tts
            tts.speak(message)
            self._last_spoken_time[alert_type] = now
            return True
        except Exception:
            # TTS failed - disable it to prevent log spam
            self._tts_available = False
            return False

    def speak_emergency(self, custom_message=None):
        """Speak emergency alert (bypasses normal cooldown, uses shorter one).

        Args:
            custom_message: Optional custom message.

        Returns:
            True if spoken.
        """
        if not config.VOICE_ENABLED or not self._tts_available:
            return False

        now = time.time()
        last_time = self._last_spoken_time.get('emergency', 0.0)
        # Emergency uses a shorter cooldown (2 seconds)
        if now - last_time < 2.0:
            return False

        message = custom_message or config.VOICE_MSG_EMERGENCY

        try:
            from plyer import tts
            tts.speak(message)
            self._last_spoken_time['emergency'] = now
            return True
        except Exception:
            self._tts_available = False
            return False

    def speak_emergency_contact(self):
        """Notify that emergency contacts will be notified."""
        return self.speak('emergency_contact')

    def can_speak(self, alert_type):
        """Check if a given alert type can be spoken (cooldown expired).

        Args:
            alert_type: The alert type to check.

        Returns:
            True if cooldown has expired.
        """
        now = time.time()
        last_time = self._last_spoken_time.get(alert_type, 0.0)
        return (now - last_time) >= config.VOICE_COOLDOWN

    def reset(self):
        """Reset all cooldown timers."""
        self._last_spoken_time.clear()

    def release(self):
        """Clean up TTS resources."""
        self._tts_available = False
