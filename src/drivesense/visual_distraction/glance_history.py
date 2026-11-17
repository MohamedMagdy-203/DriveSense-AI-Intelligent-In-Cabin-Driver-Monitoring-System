"""Persistent history of completed glance events."""

from __future__ import annotations

from src.visual_distraction.glance_tracker import GlanceEvent


class GlanceHistory:
    """Store completed glance events without applying retention rules."""

    def __init__(self) -> None:
        self._events: list[GlanceEvent] = []

    def add(self, event: GlanceEvent) -> None:
        """Append a completed event to the history."""
        self._events.append(event)

    def get_all(self) -> tuple[GlanceEvent, ...]:
        """Return the complete history as an immutable snapshot."""
        return tuple(self._events)

    def get_recent(
        self,
        start_time: float,
        end_time: float,
    ) -> tuple[GlanceEvent, ...]:
        """Return events that overlap the inclusive requested time range."""
        if start_time > end_time:
            raise ValueError("start_time must not be greater than end_time.")
        return tuple(
            event
            for event in self._events
            if event.start_time <= end_time and event.end_time >= start_time
        )
