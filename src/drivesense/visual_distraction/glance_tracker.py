"""Track glances away from the camera reference."""

from __future__ import annotations

import time
from dataclasses import dataclass

from drivesense.visual_distraction.assessment import GazeAssessmentStatus


@dataclass(frozen=True)
class GlanceEvent:
    """A completed period during which gaze was off the reference."""

    start_time: float
    end_time: float
    duration_seconds: float


class GlanceTracker:
    """Track one active off-reference glance at a time."""

    def __init__(self) -> None:
        self._start_time: float | None = None

    @property
    def active_start_time(self) -> float | None:
        """Return the start time of the active glance, if any."""
        return self._start_time

    def update(self, status: GazeAssessmentStatus) -> GlanceEvent | None:
        """Update the tracker and return a glance when it is closed."""
        timestamp = time.monotonic()

        if status is GazeAssessmentStatus.OFF_REFERENCE:
            if self._start_time is None:
                self._start_time = timestamp
            return None

        if status in (
            GazeAssessmentStatus.ON_REFERENCE,
            GazeAssessmentStatus.UNAVAILABLE,
        ):
            if self._start_time is None:
                return None
            return self._close_event(timestamp)

        raise ValueError(
            "GlanceTracker requires ON_REFERENCE, OFF_REFERENCE, "
            "or UNAVAILABLE status."
        )

    def _close_event(self, end_time: float) -> GlanceEvent:
        if self._start_time is None:
            raise RuntimeError("Cannot close a glance when none is active.")
        event = GlanceEvent(
            start_time=self._start_time,
            end_time=end_time,
            duration_seconds=end_time - self._start_time,
        )
        self._start_time = None
        return event
