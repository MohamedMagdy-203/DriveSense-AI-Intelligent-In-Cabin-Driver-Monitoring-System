"""Feature extraction and temporal policy for drowsiness monitoring."""

from __future__ import annotations

from drivesense.config import DrowsinessConfig
from drivesense.drowsiness.metrics import (
    PerclosWindow,
    calibrated_closure_score,
)
from drivesense.face.runtime import EAR_POINTS, eye_openness
from drivesense.integration_contract import (
    DrowsinessFrameStatus,
    DrowsinessObservation,
    FaceFrameStatus,
)


class DrowsinessAnalyzer:
    """Evaluate landmark eye openness and PERCLOS from face observations."""

    def __init__(self, config: DrowsinessConfig) -> None:
        self._config = config
        self._perclos = PerclosWindow(
            int(config.perclos_window_seconds * 1000)
        )
        self._prolonged_closure_test_ms = int(
            config.prolonged_closure_test_seconds * 1000
        )
        self._blink_exclusion_ms = int(
            config.blink_exclusion_seconds * 1000
        )
        self._closure_started_ms: int | None = None
        self.last_error: Exception | None = None

    def update(
        self,
        face_status: FaceFrameStatus,
        face_landmarks: tuple[object, ...] | list[object] | None,
        timestamp_ms: int,
    ) -> DrowsinessObservation:
        if face_status is FaceFrameStatus.UNAVAILABLE:
            self._closure_started_ms = None
            perclos = self._perclos.update(timestamp_ms, None)
            return DrowsinessObservation(
                DrowsinessFrameStatus.UNAVAILABLE,
                perclos_percent=perclos,
            )
        if face_status is FaceFrameStatus.NO_FACE:
            self._closure_started_ms = None
            perclos = self._perclos.update(timestamp_ms, None)
            return DrowsinessObservation(
                DrowsinessFrameStatus.NO_FACE,
                perclos_percent=perclos,
            )
        if face_landmarks is None:
            perclos = self._perclos.update(timestamp_ms, None)
            return DrowsinessObservation(
                DrowsinessFrameStatus.UNAVAILABLE,
                perclos_percent=perclos,
            )

        try:
            face = list(face_landmarks)
            right_openness = eye_openness(face, EAR_POINTS["right_eye"])
            left_openness = eye_openness(face, EAR_POINTS["left_eye"])
            openness = (right_openness + left_openness) / 2
            closure_score = calibrated_closure_score(
                openness,
                self._config.open_openness_baseline,
                self._config.closed_openness_baseline,
            )
            self.last_error = None
        except (IndexError, KeyError, ValueError) as exc:
            self.last_error = exc
            perclos = self._perclos.update(timestamp_ms, None)
            return DrowsinessObservation(
                DrowsinessFrameStatus.UNAVAILABLE,
                perclos_percent=perclos,
            )

        closed = (
            closure_score >= self._config.closure_score_threshold
        )
        if closed:
            if self._closure_started_ms is None:
                self._closure_started_ms = timestamp_ms
        else:
            self._closure_started_ms = None

        perclos_closed = (
            closed
            and self._closure_started_ms is not None
            and timestamp_ms - self._closure_started_ms
            > self._blink_exclusion_ms
        )
        perclos = self._perclos.update(timestamp_ms, perclos_closed)
        if closed:
            closure_duration_ms = (
                timestamp_ms - self._closure_started_ms
                if self._closure_started_ms is not None
                else 0
            )
            if closure_duration_ms >= self._prolonged_closure_test_ms:
                status = DrowsinessFrameStatus.PROLONGED_CLOSURE_TEST
            else:
                status = DrowsinessFrameStatus.CLOSED
        else:
            status = DrowsinessFrameStatus.OPEN
        return DrowsinessObservation(
            status,
            perclos_percent=perclos,
            closure_score=closure_score,
        )
