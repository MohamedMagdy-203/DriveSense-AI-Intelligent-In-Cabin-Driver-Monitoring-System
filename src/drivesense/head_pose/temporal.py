"""Timestamped short-term history for head pose estimates."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from experiments.head_pose.head_pose import (
    HeadPoseEstimate,
    HeadPoseStatus,
)


@dataclass(frozen=True)
class HeadPoseSample:
    """One valid head pose measurement stored in the temporal history."""

    timestamp_monotonic: float
    x_deg: float
    y_deg: float
    z_deg: float
    magnitude_deg: float


@dataclass(frozen=True)
class TemporalState:
    """Current measurement state and the retained valid history."""

    current_timestamp_monotonic: float
    current_estimate: HeadPoseEstimate
    history: tuple[HeadPoseSample, ...]


class HeadPoseTemporalAnalyzer:
    """Track valid head pose estimates over a short rolling time window."""

    def __init__(self, window_seconds: float = 2.0) -> None:
        if window_seconds <= 0:
            raise ValueError("The temporal history window must be positive.")
        self.window_seconds = window_seconds
        self._history: deque[HeadPoseSample] = deque()
        self._current_estimate = HeadPoseEstimate(HeadPoseStatus.NO_FACE)
        self._current_timestamp_monotonic = time.monotonic()

    @property
    def current_estimate(self) -> HeadPoseEstimate:
        return self._current_estimate

    @property
    def current_timestamp_monotonic(self) -> float:
        return self._current_timestamp_monotonic

    @property
    def history(self) -> tuple[HeadPoseSample, ...]:
        return tuple(self._history)

    def update(self, estimate: HeadPoseEstimate) -> TemporalState:
        """Store a valid estimate and update the current measurement state."""
        timestamp = time.monotonic()
        self._current_timestamp_monotonic = timestamp
        self._current_estimate = estimate

        if estimate.status is HeadPoseStatus.OK:
            values = estimate.rotation_vector_degrees
            if values is None or estimate.magnitude_deg is None:
                raise ValueError(
                    "An OK head pose estimate must contain all rotation values."
                )
            self._history.append(
                HeadPoseSample(
                    timestamp_monotonic=timestamp,
                    x_deg=values[0],
                    y_deg=values[1],
                    z_deg=values[2],
                    magnitude_deg=estimate.magnitude_deg,
                )
            )

        cutoff = timestamp - self.window_seconds
        while (
            self._history
            and self._history[0].timestamp_monotonic < cutoff
        ):
            self._history.popleft()

        return TemporalState(
            current_timestamp_monotonic=timestamp,
            current_estimate=estimate,
            history=self.history,
        )
