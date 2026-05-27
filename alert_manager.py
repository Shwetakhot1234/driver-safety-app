"""Alert Manager for the mobile app.

Replaces the desktop pygame-based alert system with:
- Kivy Sound for audio beeps (via temp WAV files)
- plyer TTS for voice alerts (via VoiceAssistant)
- Visual alert data for the UI layer to render

The actual visual rendering is handled by the UI dashboard module,
which reads alert state from this manager.
"""

import time
import os
import tempfile
import numpy as np

import config
from alerts.voice_assistant import VoiceAssistant


class AlertManager:
    """Manages audio beeps and voice alerts for the mobile app."""

    def __init__(self):
        self._last_alert_time = {
            'drowsy': 0.0,
            'yawning': 0.0,
            'distracted': 0.0,
            'phone': 0.0,
        }
        # Separate cooldown for beeps (faster) vs voice (slower)
        self._last_beep_time = {
            'drowsy': 0.0,
            'yawning': 0.0,
            'distracted': 0.0,
            'phone': 0.0,
        }
        # Current alert states (for UI to read)
        self.active_alerts = {
            'drowsy': False,
            'yawning': False,
            'distracted': False,
            'phone': False,
            'emergency': False,
            'eyes_closed': False,  # Early warning
        }
        # Alert messages (for UI overlay text)
        self.alert_messages = {
            'drowsy': "",
            'yawning': "",
            'distracted': "",
            'phone': "",
            'emergency': "",
            'eyes_closed': "",
        }
        self._voice = VoiceAssistant()
        self._kivy_sound_available = False
        self._beep_files = {}  # Cache of temp WAV file paths
        self._current_loop_sound = None  # Currently looping beep sound
        self._init_kivy_audio()

    def _init_kivy_audio(self):
        """Initialize Kivy audio for beep sounds.

        Pre-generates beep WAV files so they can be played instantly
        when an alert triggers. Kivy's audio_sdl2 provider requires
        file paths (not BytesIO objects).
        """
        try:
            from kivy.core.audio import SoundLoader
            self._kivy_sound_available = True
            # Pre-generate all beep sounds as temp WAV files
            self._generate_all_beeps()
            print("[INFO] Kivy audio ready for alert sounds.")
        except Exception as e:
            print(f"[WARNING] Kivy audio not available: {e}. Using voice-only alerts.")
            self._kivy_sound_available = False

    def _generate_all_beeps(self):
        """Pre-generate beep WAV files for each alert type."""
        sample_rate = 22050
        duration_ms = config.ALERT_BEEP_DURATION
        n_samples = int(sample_rate * duration_ms / 1000.0)

        beep_configs = {
            'drowsy': ('siren', 800),
            'phone': ('triple', 1000),
            'yawning': ('double', 700),
            'distracted': ('single', 600),
        }

        for alert_type, (wave_type, freq) in beep_configs.items():
            if wave_type == 'siren':
                wave_data = self._generate_siren(sample_rate, n_samples, freq)
            elif wave_type == 'triple':
                wave_data = self._generate_triple_beep(sample_rate, n_samples, freq)
            elif wave_type == 'double':
                wave_data = self._generate_double_beep(sample_rate, n_samples, freq)
            else:
                wave_data = self._generate_single_beep(sample_rate, n_samples, freq)

            filepath = self._save_wav_temp(wave_data, sample_rate, alert_type)
            if filepath:
                self._beep_files[alert_type] = filepath

    def _should_alert(self, alert_type):
        """Check if enough time has passed since last VOICE alert (cooldown).

        Args:
            alert_type: Type of alert.

        Returns:
            True if voice alert should be triggered.
        """
        now = time.time()
        last_time = self._last_alert_time.get(alert_type, 0.0)
        if now - last_time >= config.ALERT_COOLDOWN:
            self._last_alert_time[alert_type] = now
            return True
        return False

    def _should_beep(self, alert_type):
        """Check if enough time has passed since last BEEP (shorter cooldown).

        Beeps repeat much faster than voice alerts for continuous
        warning while a condition persists.

        Args:
            alert_type: Type of alert.

        Returns:
            True if beep should be played.
        """
        now = time.time()
        last_time = self._last_beep_time.get(alert_type, 0.0)
        # Drowsy/phone: faster beep (0.5s), others: 0.8s
        beep_cooldown = 0.5 if alert_type in ('drowsy', 'phone') else 0.8
        if now - last_time >= beep_cooldown:
            self._last_beep_time[alert_type] = now
            return True
        return False

    def trigger_drowsy_alert(self):
        """Trigger drowsiness alert: beep + voice."""
        beep_played = False
        if self._should_beep('drowsy'):
            self._play_beep('drowsy')
            beep_played = True
        if self._should_alert('drowsy'):
            self._voice.speak('drowsy')
        return beep_played

    def trigger_yawn_alert(self):
        """Trigger yawn alert: beep + voice."""
        beep_played = False
        if self._should_beep('yawning'):
            self._play_beep('yawning')
            beep_played = True
        if self._should_alert('yawning'):
            self._voice.speak('fatigue_warning')
        return beep_played

    def trigger_distraction_alert(self):
        """Trigger distraction alert: beep + voice."""
        beep_played = False
        if self._should_beep('distracted'):
            self._play_beep('distracted')
            beep_played = True
        if self._should_alert('distracted'):
            self._voice.speak('distraction')
        return beep_played

    def trigger_phone_alert(self):
        """Trigger phone usage alert: beep + voice."""
        beep_played = False
        if self._should_beep('phone'):
            self._play_beep('phone')
            beep_played = True
        if self._should_alert('phone'):
            self._voice.speak('phone')
        return beep_played

    def trigger_emergency_alert(self, message=None):
        """Trigger emergency alert: urgent beep + voice + UI state.

        Args:
            message: Optional custom message.
        """
        self.active_alerts['emergency'] = True
        self.alert_messages['emergency'] = message or "EMERGENCY - Critical Fatigue"
        # Emergency beeps play faster
        if self._should_beep('drowsy'):
            self._play_beep('drowsy')
        self._voice.speak_emergency(message)

    def clear_emergency_alert(self):
        """Clear the emergency alert state."""
        self.active_alerts['emergency'] = False
        self.alert_messages['emergency'] = ""

    def update_alert_states(self, drowsiness_result, distraction_result, fatigue_result):
        """Update alert states based on detection results.

        Called each frame. The UI reads active_alerts and alert_messages
        to render overlays.

        Args:
            drowsiness_result: Dict from DrowsinessDetector.
            distraction_result: Dict from DistractionDetector.
            fatigue_result: Dict from FatigueAnalyzer.
        """
        is_drowsy = drowsiness_result.get('is_drowsy', False)
        is_yawning = drowsiness_result.get('is_yawning', False)
        is_distracted = distraction_result.get('is_distracted', False)
        is_phone = distraction_result.get('is_phone_usage', False)
        is_eyes_closed = drowsiness_result.get('eyes_closed', False)

        # Update active alert states
        self.active_alerts['drowsy'] = is_drowsy
        self.active_alerts['yawning'] = is_yawning
        self.active_alerts['distracted'] = is_distracted
        self.active_alerts['phone'] = is_phone
        self.active_alerts['eyes_closed'] = is_eyes_closed

        # Update alert messages
        if is_drowsy:
            self.alert_messages['drowsy'] = "DROWSINESS DETECTED - Wake up!"
        else:
            self.alert_messages['drowsy'] = ""

        if is_eyes_closed and not is_drowsy:
            self.alert_messages['eyes_closed'] = "EYES CLOSING - Stay alert!"
        else:
            self.alert_messages['eyes_closed'] = ""

        if is_yawning:
            self.alert_messages['yawning'] = "YAWNING DETECTED - Take a break"
        else:
            self.alert_messages['yawning'] = ""

        if is_distracted:
            self.alert_messages['distracted'] = "DISTRACTED - Focus on driving"
        else:
            self.alert_messages['distracted'] = ""

        if is_phone:
            self.alert_messages['phone'] = "PHONE USAGE - Eyes on the road!"
        else:
            self.alert_messages['phone'] = ""

        # Trigger alerts with cooldown - all conditions beep independently
        if is_drowsy:
            self.trigger_drowsy_alert()
        elif is_eyes_closed:
            # Early warning beep for eye closure (lighter beep)
            if self._should_beep('drowsy'):
                self._play_beep('distracted')  # Softer beep for early warning
        if is_yawning:
            self.trigger_yawn_alert()
        if is_phone:
            self.trigger_phone_alert()
        if is_distracted:
            self.trigger_distraction_alert()

    def get_highest_alert(self):
        """Get the highest priority active alert.

        Returns:
            Tuple of (alert_type, message) or (None, None).
        """
        priority_order = ['emergency', 'drowsy', 'phone', 'yawning', 'distracted']
        for alert_type in priority_order:
            if self.active_alerts.get(alert_type, False):
                return alert_type, self.alert_messages.get(alert_type, "")
        return None, None

    def _save_wav_temp(self, wave_data, sample_rate, alert_type):
        """Save wave data to a temporary WAV file.

        Args:
            wave_data: numpy int16 array of audio samples.
            sample_rate: Sample rate in Hz.
            alert_type: Alert type name for filename.

        Returns:
            Path to the temp WAV file, or None on error.
        """
        try:
            import wave
            import struct

            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, f"driver_safety_{alert_type}.wav")

            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                for sample in wave_data:
                    wf.writeframes(struct.pack('<h', int(sample)))

            return filepath
        except Exception as e:
            print(f"[WARNING] Could not save beep file for {alert_type}: {e}")
            return None

    def _play_beep(self, alert_type):
        """Play a pre-generated beep sound via Kivy SoundLoader.

        Args:
            alert_type: Type of alert to determine beep pattern.
        """
        if not self._kivy_sound_available:
            return

        try:
            from kivy.core.audio import SoundLoader

            filepath = self._beep_files.get(alert_type)
            if not filepath or not os.path.exists(filepath):
                # Fallback: try drowsy beep
                filepath = self._beep_files.get('drowsy')

            if filepath and os.path.exists(filepath):
                sound = SoundLoader.load(filepath)
                if sound:
                    sound.play()
                    return

            print(f"[WARNING] No beep file for {alert_type}")

        except Exception as e:
            print(f"[WARNING] Could not play beep: {e}")

    @staticmethod
    def _generate_single_beep(sample_rate, n_samples, freq):
        """Generate a single ascending beep."""
        t = np.linspace(0, n_samples / sample_rate, n_samples, endpoint=False)
        freq_sweep = np.linspace(freq, freq + 200, n_samples)
        wave = np.sin(2 * np.pi * freq_sweep * t)
        # Apply envelope
        fade = min(int(sample_rate * 0.01), n_samples // 8)
        wave[:fade] *= np.linspace(0, 1, fade)
        wave[-fade:] *= np.linspace(1, 0, fade)
        return (wave * 32767 * 0.8).astype(np.int16)

    @staticmethod
    def _generate_double_beep(sample_rate, n_samples, freq):
        """Generate two short beeps with a gap."""
        seg = n_samples // 4
        t1 = np.linspace(0, seg / sample_rate, seg, endpoint=False)
        silence = np.zeros(seg)
        t2 = np.linspace(0, seg / sample_rate, seg, endpoint=False)
        tail = np.zeros(n_samples - 3 * seg)
        beep1 = np.sin(2 * np.pi * freq * t1)
        beep2 = np.sin(2 * np.pi * freq * t2)
        wave = np.concatenate([beep1, silence, beep2, tail])
        return (wave * 32767 * 0.8).astype(np.int16)

    @staticmethod
    def _generate_triple_beep(sample_rate, n_samples, freq):
        """Generate three rapid beeps."""
        seg = n_samples // 6
        t = np.linspace(0, seg / sample_rate, seg, endpoint=False)
        gap = np.zeros(seg // 3)
        tail = np.zeros(max(0, n_samples - 3 * seg - 2 * (seg // 3)))
        beep1 = np.sin(2 * np.pi * freq * t)
        beep2 = np.sin(2 * np.pi * freq * t)
        beep3 = np.sin(2 * np.pi * (freq + 200) * t)
        wave = np.concatenate([beep1, gap, beep2, gap, beep3, tail])
        # Pad if needed
        if len(wave) < n_samples:
            wave = np.pad(wave, (0, n_samples - len(wave)))
        else:
            wave = wave[:n_samples]
        return (wave * 32767 * 0.8).astype(np.int16)

    @staticmethod
    def _generate_siren(sample_rate, n_samples, base_freq):
        """Generate a siren (alternating high-low tones)."""
        third = n_samples // 3
        t1 = np.linspace(0, third / sample_rate, third, endpoint=False)
        t2 = np.linspace(0, third / sample_rate, third, endpoint=False)
        t3 = np.linspace(0, (n_samples - 2 * third) / sample_rate,
                         n_samples - 2 * third, endpoint=False)
        wave1 = np.sin(2 * np.pi * (base_freq + 100) * t1)
        wave2 = np.sin(2 * np.pi * (base_freq - 200) * t2)
        wave3 = np.sin(2 * np.pi * (base_freq + 100) * t3)
        wave = np.concatenate([wave1, wave2, wave3])
        # Pad or trim
        if len(wave) < n_samples:
            wave = np.pad(wave, (0, n_samples - len(wave)))
        else:
            wave = wave[:n_samples]
        return (wave * 32767 * 0.8).astype(np.int16)

    def reset(self):
        """Reset all alert states and cooldowns."""
        for key in self._last_alert_time:
            self._last_alert_time[key] = 0.0
        for key in self._last_beep_time:
            self._last_beep_time[key] = 0.0
        for key in self.active_alerts:
            self.active_alerts[key] = False
        for key in self.alert_messages:
            self.alert_messages[key] = ""
        self._voice.reset()

    def release(self):
        """Release all audio resources and clean up temp files."""
        self._voice.release()
        # Clean up temp beep files
        for filepath in self._beep_files.values():
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
        self._beep_files.clear()
