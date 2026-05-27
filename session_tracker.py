"""Session Tracker for driver analytics.

Tracks all events and statistics during a monitoring session:
- Drowsiness events
- Yawning events
- Phone usage events
- Distraction events
- Fatigue level history
- Session duration

Data is used by report_generator.py for end-of-session reports.
"""

import time

import config


class SessionTracker:
    """Tracks session analytics for driver monitoring."""

    def __init__(self):
        self._start_time = None
        self._end_time = None
        self._is_active = False

        # Event counters
        self.total_yawns = 0
        self.drowsiness_events = 0
        self.phone_usage_events = 0
        self.distraction_count = 0

        # Peak values
        self.max_fatigue_score = 0.0
        self.max_fatigue_level = "SAFE"

        # Running averages
        self._ear_sum = 0.0
        self._ear_count = 0
        self._mar_sum = 0.0
        self._mar_count = 0

        # Event log: list of (timestamp, event_type, details) tuples
        self.event_log = []

        # Fatigue history: list of (timestamp, fatigue_score) for charting
        self.fatigue_history = []

        # Previous states for edge detection
        self._prev_drowsy = False
        self._prev_yawning = False
        self._prev_distracted = False
        self._prev_phone = False

    def start_session(self):
        """Start a new monitoring session."""
        self._start_time = time.time()
        self._end_time = None
        self._is_active = True
        self._log_event("SESSION_START", "Monitoring session started")

    def stop_session(self):
        """Stop the current session."""
        self._end_time = time.time()
        self._is_active = False
        self._log_event("SESSION_END", "Monitoring session ended")

    @property
    def session_duration(self):
        """Get session duration in seconds.

        Returns:
            Float duration in seconds, 0 if not started.
        """
        if self._start_time is None:
            return 0.0
        end = self._end_time or time.time()
        return end - self._start_time

    @property
    def is_active(self):
        """Whether a session is currently active."""
        return self._is_active

    def update(self, drowsiness_result, distraction_result, fatigue_result):
        """Update session tracker with current frame results.

        Call this every frame during active monitoring.

        Args:
            drowsiness_result: Dict from DrowsinessDetector.
            distraction_result: Dict from DistractionDetector.
            fatigue_result: Dict from FatigueAnalyzer.
        """
        if not self._is_active:
            return

        # --- Track drowsiness events (edge detection) ---
        is_drowsy = drowsiness_result.get('is_drowsy', False)
        if is_drowsy and not self._prev_drowsy:
            self.drowsiness_events += 1
            self._log_event("DROWSINESS", "Drowsiness detected",
                           ear=drowsiness_result.get('ear', 0))
        self._prev_drowsy = is_drowsy

        # --- Track yawning events (edge detection) ---
        is_yawning = drowsiness_result.get('is_yawning', False)
        if is_yawning and not self._prev_yawning:
            self.total_yawns += 1
            self._log_event("YAWN", "Yawning detected",
                           mar=drowsiness_result.get('mar', 0))
        self._prev_yawning = is_yawning

        # --- Track distraction events (edge detection) ---
        is_distracted = distraction_result.get('is_distracted', False)
        if is_distracted and not self._prev_distracted:
            self.distraction_count += 1
            self._log_event("DISTRACTION", "Distraction detected")
        self._prev_distracted = is_distracted

        # --- Track phone usage events (edge detection) ---
        is_phone = distraction_result.get('is_phone_usage', False)
        if is_phone and not self._prev_phone:
            self.phone_usage_events += 1
            self._log_event("PHONE_USAGE", "Phone usage detected")
        self._prev_phone = is_phone

        # --- Track fatigue score ---
        fatigue_score = fatigue_result.get('fatigue_score', 0)
        risk_level = fatigue_result.get('risk_level', 'SAFE')

        # Record fatigue history (sample every ~1 second)
        if len(self.fatigue_history) == 0 or (
            time.time() - self.fatigue_history[-1][0] >= 1.0
        ):
            self.fatigue_history.append((time.time(), fatigue_score))

        # Update max fatigue
        if fatigue_score > self.max_fatigue_score:
            self.max_fatigue_score = fatigue_score
            self.max_fatigue_level = risk_level

        # --- Running averages ---
        ear = drowsiness_result.get('ear', 0)
        mar = drowsiness_result.get('mar', 0)
        self._ear_sum += ear
        self._ear_count += 1
        self._mar_sum += mar
        self._mar_count += 1

    def _log_event(self, event_type, description, **details):
        """Log an event with timestamp and optional details.

        Args:
            event_type: Type of event (e.g. 'DROWSINESS', 'YAWN').
            description: Human-readable description.
            **details: Additional key-value details.
        """
        self.event_log.append({
            'timestamp': time.time(),
            'type': event_type,
            'description': description,
            'details': details,
        })

    def get_summary(self):
        """Get session summary statistics.

        Returns:
            dict with all session analytics.
        """
        avg_ear = self._ear_sum / self._ear_count if self._ear_count > 0 else 0
        avg_mar = self._mar_sum / self._mar_count if self._mar_count > 0 else 0

        return {
            'session_duration': self.session_duration,
            'total_yawns': self.total_yawns,
            'drowsiness_events': self.drowsiness_events,
            'phone_usage_events': self.phone_usage_events,
            'distraction_count': self.distraction_count,
            'max_fatigue_score': self.max_fatigue_score,
            'max_fatigue_level': self.max_fatigue_level,
            'average_ear': round(avg_ear, 3),
            'average_mar': round(avg_mar, 3),
            'event_count': len(self.event_log),
        }

    def reset(self):
        """Reset all session data."""
        self._start_time = None
        self._end_time = None
        self._is_active = False
        self.total_yawns = 0
        self.drowsiness_events = 0
        self.phone_usage_events = 0
        self.distraction_count = 0
        self.max_fatigue_score = 0.0
        self.max_fatigue_level = "SAFE"
        self._ear_sum = 0.0
        self._ear_count = 0
        self._mar_sum = 0.0
        self._mar_count = 0
        self.event_log.clear()
        self.fatigue_history.clear()
        self._prev_drowsy = False
        self._prev_yawning = False
        self._prev_distracted = False
        self._prev_phone = False
