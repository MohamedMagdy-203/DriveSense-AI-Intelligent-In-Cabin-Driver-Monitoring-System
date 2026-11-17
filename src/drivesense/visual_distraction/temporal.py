"""Temporal analysis of completed and active off-reference glances."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from drivesense.config import load_config
from drivesense.visual_distraction.assessment import GazeAssessmentStatus
from drivesense.visual_distraction.glance_history import GlanceHistory


class DistractionStatus(str, Enum):
    """Preliminary temporal assessment of visual distraction."""

    POTENTIAL_DISTRACTION = "POTENTIAL_DISTRACTION"
    ATTENTIVE = "ATTENTIVE"
    UNDETERMINED = "UNDETERMINED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class DistractionAssessment:
    """Result of one temporal distraction analysis update."""

    status: DistractionStatus


class TemporalDistractionAnalyzer:
    """Evaluate glance duration and repetition over time."""

    _CONFIG = load_config().temporal
    LONG_GLANCE_SECONDS = _CONFIG.long_glance_seconds
    WINDOW_SECONDS = _CONFIG.glance_window_seconds
    REENGAGEMENT_SECONDS = _CONFIG.reengagement_seconds
    CUMULATIVE_GLANCE_SECONDS = _CONFIG.cumulative_glance_seconds

    def __init__(self) -> None:
        self._reference_start_time: float | None = None
        self._reengagement_applied = False
        self._last_reengagement_time: float | None = None

    def update(
        self,
        history: GlanceHistory,
        active_start_time: float | None,
        current_status: GazeAssessmentStatus,
    ) -> DistractionAssessment:
        """Analyze the current glance state and recent completed events."""
        now = time.monotonic()

        if current_status is GazeAssessmentStatus.UNAVAILABLE:
            self._reset_reference_tracking()
            return DistractionAssessment(DistractionStatus.UNAVAILABLE)

        if current_status is GazeAssessmentStatus.UNDETERMINED:
            return DistractionAssessment(DistractionStatus.UNDETERMINED)

        if current_status is GazeAssessmentStatus.ON_REFERENCE:
            self._track_reengagement(now)
        else:
            self._reset_reference_tracking()
            if active_start_time is None:
                return DistractionAssessment(DistractionStatus.UNDETERMINED)

        window_start = now - self.WINDOW_SECONDS
        if self._last_reengagement_time is not None:
            window_start = max(window_start, self._last_reengagement_time)

        recent_events = history.get_recent(window_start, now)
        active_duration = (
            0.0
            if active_start_time is None
            else max(0.0, now - active_start_time)
        )
        if active_duration >= self.LONG_GLANCE_SECONDS:
            return DistractionAssessment(DistractionStatus.POTENTIAL_DISTRACTION)
        if any(
            event.duration_seconds >= self.LONG_GLANCE_SECONDS
            for event in recent_events
        ):
            return DistractionAssessment(DistractionStatus.POTENTIAL_DISTRACTION)

        closed_duration = sum(
            max(
                0.0,
                min(event.end_time, now)
                - max(event.start_time, window_start),
            )
            for event in recent_events
        )
        active_window_duration = (
            0.0
            if active_start_time is None
            else max(0.0, now - max(active_start_time, window_start))
        )
        if closed_duration + active_window_duration >= self.CUMULATIVE_GLANCE_SECONDS:
            return DistractionAssessment(DistractionStatus.POTENTIAL_DISTRACTION)

        if current_status is GazeAssessmentStatus.ON_REFERENCE:
            return DistractionAssessment(DistractionStatus.ATTENTIVE)
        return DistractionAssessment(DistractionStatus.UNDETERMINED)

    def _track_reengagement(self, now: float) -> None:
        if self._reference_start_time is None:
            self._reference_start_time = now
            self._reengagement_applied = False
        if (
            not self._reengagement_applied
            and now - self._reference_start_time >= self.REENGAGEMENT_SECONDS
        ):
            self._last_reengagement_time = now
            self._reengagement_applied = True

    def _reset_reference_tracking(self) -> None:
        self._reference_start_time = None
        self._reengagement_applied = False
