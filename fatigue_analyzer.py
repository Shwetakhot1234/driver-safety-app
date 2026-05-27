"""Predictive Fatigue Analysis System.

Analyzes multiple fatigue indicators over time to predict driver fatigue
BEFORE it becomes dangerous. Uses:

- Blink frequency tracking over rolling windows
- EAR trend analysis (linear regression slope)
- Yawning frequency tracking
- Distraction duration accumulation
- Phone usage patterns
- Adaptive baseline learning (learns normal patterns in first 2 minutes)

Composite fatigue score: 0-100
- SAFE: 0-30
- WARNING: 31-60
- DANGEROUS: 61-100
"""

import time
import numpy as np
from collections import deque

import config


class FatigueAnalyzer:
    """Predictive fatigue analysis with adaptive baseline learning."""

    # Risk level constants
    RISK_SAFE = "SAFE"
    RISK_WARNING = "WARNING"
    RISK_DANGEROUS = "DANGEROUS"

    def __init__(self):
        # Timestamps for event tracking
        self._start_time = time.time()
        self._blink_times = deque(maxlen=500)        # Timestamps of blink events
        self._yawn_times = deque(maxlen=200)          # Timestamps of yawn events
        self._phone_times = deque(maxlen=200)         # Timestamps of phone usage starts
        self._distraction_times = deque(maxlen=200)   # Timestamps of distraction starts

        # EAR history for trend analysis: (timestamp, ear_value)
        self._ear_history = deque(maxlen=2000)

        # Distraction/phone cumulative duration tracking
        self._distraction_start = None
        self._total_distraction_duration = 0.0
        self._phone_start = None
        self._total_phone_duration = 0.0

        # Adaptive baseline (learned during first N seconds)
        self._baseline_ear_values = deque(maxlen=500)
        self._baseline_mar_values = deque(maxlen=500)
        self._baseline_ear_mean = config.EAR_THRESHOLD  # Default until learned
        self._baseline_mar_mean = config.MAR_THRESHOLD
        self._baseline_learned = False

        # Previous blink state for edge detection
        self._prev_eyes_closed = False

        # Results cache
        self.fatigue_score = 0.0
        self.risk_level = self.RISK_SAFE
        self.fatigue_trend = 0.0      # Positive = getting worse
        self.blink_rate = 0.0         # Blinks per minute
        self.yawn_rate = 0.0          # Yawns per minute
        self.attention_score = 100.0  # 0-100, 100 = fully attentive

    def update(self, ear, mar, is_drowsy, is_yawning, is_distracted, is_phone_usage):
        """Update fatigue analysis with current frame data.

        Args:
            ear: Current Eye Aspect Ratio.
            mar: Current Mouth Aspect Ratio.
            is_drowsy: Whether drowsiness is detected.
            is_yawning: Whether yawning is detected.
            is_distracted: Whether distraction is detected.
            is_phone_usage: Whether phone usage is detected.

        Returns:
            dict with fatigue analysis results.
        """
        now = time.time()
        elapsed = now - self._start_time

        # --- Adaptive Baseline Learning ---
        if not self._baseline_learned and elapsed < config.ADAPTIVE_BASELINE_DURATION:
            self._baseline_ear_values.append(ear)
            self._baseline_mar_values.append(mar)
        elif not self._baseline_learned and elapsed >= config.ADAPTIVE_BASELINE_DURATION:
            if len(self._baseline_ear_values) > 10:
                self._baseline_ear_mean = float(np.mean(self._baseline_ear_values))
                self._baseline_mar_mean = float(np.mean(self._baseline_mar_values))
            self._baseline_learned = True

        # --- Blink Detection (edge: eyes were open, now closed) ---
        eyes_closed = ear < config.EAR_THRESHOLD
        if eyes_closed and not self._prev_eyes_closed:
            self._blink_times.append(now)
        self._prev_eyes_closed = eyes_closed

        # --- Yawn Event Tracking ---
        if is_yawning:
            # Only record if last yawn was more than 2 seconds ago
            if not self._yawn_times or (now - self._yawn_times[-1]) > 2.0:
                self._yawn_times.append(now)

        # --- Phone Usage Tracking ---
        if is_phone_usage:
            if self._phone_start is None:
                self._phone_start = now
                self._phone_times.append(now)
            self._total_phone_duration = self._total_phone_duration + 0.033  # ~30fps
        else:
            self._phone_start = None

        # --- Distraction Duration Tracking ---
        if is_distracted:
            if self._distraction_start is None:
                self._distraction_start = now
                self._distraction_times.append(now)
            self._total_distraction_duration = self._total_distraction_duration + 0.033
        else:
            self._distraction_start = None

        # --- EAR History for Trend ---
        self._ear_history.append((now, ear))

        # --- Compute Blink Rate ---
        self.blink_rate = self._compute_blink_rate(now)

        # --- Compute Yawn Rate ---
        self.yawn_rate = self._compute_yawn_rate(now)

        # --- Compute EAR Trend ---
        self.fatigue_trend = self._compute_ear_trend(now)

        # --- Compute Composite Fatigue Score ---
        self.fatigue_score = self._compute_fatigue_score(
            is_drowsy, is_yawning, is_distracted, is_phone_usage
        )

        # --- Determine Risk Level ---
        if self.fatigue_score <= config.FATIGUE_SAFE_MAX:
            self.risk_level = self.RISK_SAFE
        elif self.fatigue_score <= config.FATIGUE_WARNING_MAX:
            self.risk_level = self.RISK_WARNING
        else:
            self.risk_level = self.RISK_DANGEROUS

        # --- Compute Attention Score ---
        self.attention_score = max(0.0, 100.0 - self.fatigue_score)

        return {
            'fatigue_score': self.fatigue_score,
            'risk_level': self.risk_level,
            'fatigue_trend': self.fatigue_trend,
            'blink_rate': self.blink_rate,
            'yawn_rate': self.yawn_rate,
            'attention_score': self.attention_score,
            'baseline_learned': self._baseline_learned,
            'baseline_ear': self._baseline_ear_mean,
            'total_distraction_duration': self._total_distraction_duration,
            'total_phone_duration': self._total_phone_duration,
        }

    def _compute_blink_rate(self, now):
        """Compute blink rate (blinks per minute) over the short window.

        Returns:
            Float blinks per minute.
        """
        cutoff = now - config.FATIGUE_WINDOW_SHORT
        # Count blinks within the window
        recent_blinks = sum(1 for t in self._blink_times if t > cutoff)
        # Normalize to per-minute rate
        window_minutes = config.FATIGUE_WINDOW_SHORT / 60.0
        return recent_blinks / window_minutes if window_minutes > 0 else 0.0

    def _compute_yawn_rate(self, now):
        """Compute yawn rate (yawns per minute) over the short window.

        Returns:
            Float yawns per minute.
        """
        cutoff = now - config.FATIGUE_WINDOW_SHORT
        recent_yawns = sum(1 for t in self._yawn_times if t > cutoff)
        window_minutes = config.FATIGUE_WINDOW_SHORT / 60.0
        return recent_yawns / window_minutes if window_minutes > 0 else 0.0

    def _compute_ear_trend(self, now):
        """Compute EAR trend using linear regression slope.

        A negative slope means EAR is decreasing over time (eyes getting
        more closed on average) = fatigue increasing.

        Returns:
            Float slope of EAR over time. Negative = worsening fatigue.
        """
        cutoff = now - config.EAR_TREND_WINDOW
        recent_data = [(t, e) for t, e in self._ear_history if t > cutoff]

        if len(recent_data) < 10:
            return 0.0

        times = np.array([d[0] - recent_data[0][0] for d in recent_data])
        ears = np.array([d[1] for d in recent_data])

        # Simple linear regression: ear = a + b*t
        n = len(times)
        sum_t = np.sum(times)
        sum_e = np.sum(ears)
        sum_te = np.sum(times * ears)
        sum_tt = np.sum(times * times)

        denom = n * sum_tt - sum_t * sum_t
        if abs(denom) < 1e-10:
            return 0.0

        slope = (n * sum_te - sum_t * sum_e) / denom

        # Normalize: a slope of -0.001 per second is concerning
        # We scale it so -0.001/s maps to roughly +1.0 trend score
        trend = -slope * 1000.0

        return float(trend)

    def _compute_fatigue_score(self, is_drowsy, is_yawning, is_distracted, is_phone_usage):
        """Compute composite fatigue score (0-100) from all indicators.

        Each component contributes 0-100, weighted by config weights.

        Returns:
            Float fatigue score 0-100.
        """
        # --- Blink Rate Component ---
        if self.blink_rate <= config.BLINK_RATE_NORMAL:
            blink_score = 0.0
        elif self.blink_rate >= config.BLINK_RATE_FATIGUE:
            blink_score = 100.0
        else:
            # Linear interpolation
            blink_score = (
                (self.blink_rate - config.BLINK_RATE_NORMAL)
                / (config.BLINK_RATE_FATIGUE - config.BLINK_RATE_NORMAL)
            ) * 100.0

        # --- EAR Trend Component ---
        # fatigue_trend > 0 means worsening
        if self.fatigue_trend <= 0:
            trend_score = 0.0
        elif self.fatigue_trend >= 1.0:
            trend_score = 100.0
        else:
            trend_score = self.fatigue_trend * 100.0

        # --- Yawn Rate Component ---
        if self.yawn_rate <= config.YAWN_RATE_NORMAL:
            yawn_score = 0.0
        elif self.yawn_rate >= config.YAWN_RATE_FATIGUE:
            yawn_score = 100.0
        else:
            yawn_score = (
                (self.yawn_rate - config.YAWN_RATE_NORMAL)
                / (config.YAWN_RATE_FATIGUE - config.YAWN_RATE_NORMAL)
            ) * 100.0

        # --- Distraction Duration Component ---
        # More than 30 seconds of distraction in last 5 min is concerning
        distraction_ratio = min(self._total_distraction_duration / 30.0, 1.0)
        distraction_score = distraction_ratio * 100.0
        if is_distracted:
            distraction_score = max(distraction_score, 50.0)

        # --- Phone Usage Component ---
        phone_ratio = min(self._total_phone_duration / 20.0, 1.0)
        phone_score = phone_ratio * 100.0
        if is_phone_usage:
            phone_score = max(phone_score, 60.0)

        # --- Active drowsiness/yawning bonus (immediate danger) ---
        immediate_danger = 0.0
        if is_drowsy:
            immediate_danger += 30.0
        if is_yawning:
            immediate_danger += 15.0

        # --- Adaptive baseline deviation ---
        baseline_deviation = 0.0
        if self._baseline_learned and len(self._ear_history) > 0:
            recent_ears = [e for _, e in list(self._ear_history)[-30:]]
            if recent_ears:
                avg_recent = np.mean(recent_ears)
                # If recent EAR is significantly below baseline
                deviation = self._baseline_ear_mean - avg_recent
                if deviation > 0.02:
                    baseline_deviation = min(deviation * 500, 20.0)

        # --- Weighted Composite ---
        composite = (
            config.FATIGUE_WEIGHT_BLINK * blink_score
            + config.FATIGUE_WEIGHT_EAR_TREND * trend_score
            + config.FATIGUE_WEIGHT_YAWN * yawn_score
            + config.FATIGUE_WEIGHT_DISTRACTION * distraction_score
            + config.FATIGUE_WEIGHT_PHONE * phone_score
        )

        # Add immediate danger and baseline deviation (unweighted bonus)
        composite += immediate_danger + baseline_deviation

        # Clamp to 0-100
        return float(max(0.0, min(100.0, composite)))

    def reset(self):
        """Reset all fatigue analysis state."""
        self._start_time = time.time()
        self._blink_times.clear()
        self._yawn_times.clear()
        self._phone_times.clear()
        self._distraction_times.clear()
        self._ear_history.clear()
        self._baseline_ear_values.clear()
        self._baseline_mar_values.clear()
        self._baseline_ear_mean = config.EAR_THRESHOLD
        self._baseline_mar_mean = config.MAR_THRESHOLD
        self._baseline_learned = False
        self._prev_eyes_closed = False
        self._distraction_start = None
        self._total_distraction_duration = 0.0
        self._phone_start = None
        self._total_phone_duration = 0.0
        self.fatigue_score = 0.0
        self.risk_level = self.RISK_SAFE
        self.fatigue_trend = 0.0
        self.blink_rate = 0.0
        self.yawn_rate = 0.0
        self.attention_score = 100.0
