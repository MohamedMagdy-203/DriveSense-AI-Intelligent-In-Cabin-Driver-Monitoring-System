"""Reusable timestamp-based drowsiness metrics."""

from __future__ import annotations

from collections import deque


class PerclosWindow:
    """Track closed and observed durations over a rolling time window."""

    def __init__(self, window_ms: int) -> None:
        if window_ms <= 0:
            raise ValueError("The PERCLOS window must be positive.")
        self.window_ms = window_ms
        self.segments: deque[tuple[int, int, bool]] = deque()
        self.last_timestamp_ms: int | None = None
        self.last_closed: bool | None = None

    def update(self, timestamp_ms: int, closed: bool | None) -> float:
        if (
            closed is not None
            and self.last_timestamp_ms is not None
            and self.last_closed is not None
            and timestamp_ms > self.last_timestamp_ms
        ):
            self.segments.append(
                (self.last_timestamp_ms, timestamp_ms, self.last_closed)
            )

        if closed is None:
            self.last_timestamp_ms = None
            self.last_closed = None
        else:
            self.last_timestamp_ms = timestamp_ms
            self.last_closed = closed

        window_start = timestamp_ms - self.window_ms
        while self.segments and self.segments[0][1] <= window_start:
            self.segments.popleft()

        closed_duration = 0
        observed_duration = 0
        for start_ms, end_ms, was_closed in self.segments:
            clipped_start = max(start_ms, window_start)
            if end_ms <= clipped_start:
                continue
            duration = end_ms - clipped_start
            observed_duration += duration
            if was_closed:
                closed_duration += duration

        if observed_duration == 0:
            return 0.0
        return 100 * closed_duration / observed_duration


def calibrated_closure_score(
    openness: float,
    open_baseline: float,
    closed_baseline: float,
) -> float:
    """Map calibrated openness to a clamped closure score in ``[0, 1]``."""
    baseline_range = open_baseline - closed_baseline
    if baseline_range <= 0:
        raise ValueError("Open and closed openness baselines must be ordered.")
    return min(
        1.0,
        max(0.0, (open_baseline - openness) / baseline_range),
    )
