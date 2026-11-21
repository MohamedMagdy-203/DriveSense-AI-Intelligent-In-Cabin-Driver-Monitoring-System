"""Integrated frame processing for the DriveSense monitoring prototype."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from drivesense.drowsiness.analyzer import DrowsinessAnalyzer
from drivesense.config import DrowsinessConfig, TemporalConfig
from drivesense.face.runtime import face_observation_from_result
from drivesense.head_pose.pose import HeadPoseEstimator
from drivesense.head_pose.temporal import HeadPoseTemporalAnalyzer
from drivesense.integration_contract import (
    DrowsinessFrameStatus,
    DrowsinessObservation,
    EngineFrameOutput,
    FaceObservation,
    FaceFrameStatus,
    FrameTimestamps,
    PhoneObservation,
    PhoneFrameStatus,
)
from drivesense.visual_distraction.assessment import (
    assess_driving_gaze,
)
from drivesense.visual_distraction.gaze.calibration import EyeCalibration
from drivesense.visual_distraction.gaze.classification import (
    GazeClassification,
    GazeProcessor,
)
from drivesense.visual_distraction.glance_history import GlanceHistory
from drivesense.visual_distraction.glance_tracker import GlanceTracker
from drivesense.visual_distraction.temporal import (
    TemporalDistractionAnalyzer,
)


class DriverMonitoringEngine:
    """Unify existing monitoring modules into one frame-level cycle."""

    def __init__(
        self,
        face_provider: object | None = None,
        phone_provider: object | None = None,
        gaze_calibrations: Mapping[str, EyeCalibration] | None = None,
        horizontal_signs: Mapping[str, int] | None = None,
        clock: Callable[[], float] | None = None,
        perclos_window_ms: int = 60_000,
        open_openness_baseline: float = 0.3298,
        closed_openness_baseline: float = 0.0736,
        closure_score_threshold: float = 0.8,
        blink_exclusion_ms: int = 200,
        drowsiness: DrowsinessConfig | None = None,
        temporal: TemporalConfig | None = None,
    ) -> None:
        if temporal is None:
            temporal = TemporalConfig(
                head_pose_window_seconds=2.0,
                long_glance_seconds=3.0,
                glance_window_seconds=30.0,
                reengagement_seconds=2.0,
                cumulative_glance_seconds=10.0,
            )
        if drowsiness is None:
            drowsiness = DrowsinessConfig(
                perclos_window_seconds=perclos_window_ms / 1000,
                closure_score_threshold=closure_score_threshold,
                blink_exclusion_seconds=blink_exclusion_ms / 1000,
                prolonged_closure_test_seconds=4.0,
                open_openness_baseline=open_openness_baseline,
                closed_openness_baseline=closed_openness_baseline,
            )
        else:
            perclos_window_ms = int(drowsiness.perclos_window_seconds * 1000)
            open_openness_baseline = drowsiness.open_openness_baseline
            closed_openness_baseline = drowsiness.closed_openness_baseline
            closure_score_threshold = drowsiness.closure_score_threshold
            blink_exclusion_ms = int(drowsiness.blink_exclusion_seconds * 1000)
        if perclos_window_ms <= 0:
            raise ValueError("perclos_window_ms must be positive.")
        if open_openness_baseline <= closed_openness_baseline:
            raise ValueError(
                "Open openness baseline must be above the closed baseline."
            )
        if not 0.0 <= closure_score_threshold <= 1.0:
            raise ValueError("closure_score_threshold must be between 0 and 1.")
        if blink_exclusion_ms < 0:
            raise ValueError("blink_exclusion_ms must be non-negative.")

        self._face_provider = face_provider
        self._phone_provider = phone_provider
        self._clock = clock or time.monotonic
        self._gaze_processor = GazeProcessor(
            gaze_calibrations,
            horizontal_signs,
        )
        self._drowsiness_analyzer = DrowsinessAnalyzer(drowsiness)

        self._head_pose_estimator = HeadPoseEstimator()
        self._head_pose_temporal = HeadPoseTemporalAnalyzer(
            window_seconds=temporal.head_pose_window_seconds,
            clock=self._clock
        )
        self._glance_tracker = GlanceTracker(clock=self._clock)
        self._glance_history = GlanceHistory()
        self._distraction_analyzer = TemporalDistractionAnalyzer(
            config=temporal,
            clock=self._clock
        )

        self._previous_timestamp_ms = -1
        self._is_open = False
        self._face_entered = False
        self._phone_entered = False
        self.last_gaze_error: Exception | None = None
        self.last_drowsiness_error: Exception | None = None
        self.last_face_error: Exception | None = None

    def __enter__(self) -> "DriverMonitoringEngine":
        if hasattr(self._face_provider, "__enter__"):
            self._face_provider.__enter__()
            self._face_entered = True
        try:
            if hasattr(self._phone_provider, "__enter__"):
                self._phone_provider.__enter__()
                self._phone_entered = True
        except Exception:
            if self._face_entered and hasattr(self._face_provider, "__exit__"):
                self._face_provider.__exit__(None, None, None)
                self._face_entered = False
            raise
        self._is_open = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._phone_entered and hasattr(self._phone_provider, "__exit__"):
            self._phone_provider.__exit__(exc_type, exc_value, traceback)
            self._phone_entered = False
        elif hasattr(self._phone_provider, "close"):
            self._phone_provider.close()
        if self._face_entered and hasattr(self._face_provider, "__exit__"):
            self._face_provider.__exit__(exc_type, exc_value, traceback)
            self._face_entered = False
        self._is_open = False

    def close(self) -> None:
        if hasattr(self._phone_provider, "close") and not self._phone_entered:
            self._phone_provider.close()
        elif self._phone_entered and hasattr(self._phone_provider, "__exit__"):
            self._phone_provider.__exit__(None, None, None)
            self._phone_entered = False
        if hasattr(self._face_provider, "close") and not self._face_entered:
            self._face_provider.close()
        elif self._face_entered and hasattr(self._face_provider, "__exit__"):
            self._face_provider.__exit__(None, None, None)
            self._face_entered = False
        self._is_open = False

    def update(
        self,
        frame: object,
        timestamp_ms: int,
    ) -> EngineFrameOutput:
        """Process one frame and return one independent signal bundle."""
        if timestamp_ms <= self._previous_timestamp_ms:
            raise ValueError(
                "timestamp_ms must be strictly greater than the previous frame."
            )
        self._previous_timestamp_ms = timestamp_ms
        monotonic_seconds = self._clock()

        timestamps = FrameTimestamps(
            media_pipe_ms=timestamp_ms,
            monotonic_seconds=monotonic_seconds,
        )

        result = self._process_face(frame, timestamp_ms)
        face_landmarks: tuple[object, ...] | list[object] | None = None
        if isinstance(result, FaceObservation):
            face_status = result.status
            if face_status is FaceFrameStatus.AVAILABLE:
                face_landmarks = list(result.landmarks)
                gaze = self._process_gaze(face_landmarks)
                head_result = _FaceResult(
                    face_landmarks=list(result.landmarks),
                    facial_matrix=result.facial_matrix,
                )
                head_pose = self._head_pose_estimator.update(head_result)
            else:
                gaze = None
                head_pose = self._head_pose_estimator.update(_NoFaceResult())
        elif result is None:
            face_status = FaceFrameStatus.UNAVAILABLE
            face_landmarks = None
            gaze = None
            head_pose = self._head_pose_estimator.update(
                _NoFaceResult()
            )
        else:
            face_status = FaceFrameStatus.UNAVAILABLE
            face_landmarks = None
            gaze = None
            head_pose = self._head_pose_estimator.update(_NoFaceResult())
            self.last_face_error = ValueError(
                "Face provider returned an unsupported result."
            )

        head_temporal = self._head_pose_temporal.update(head_pose)
        del head_temporal

        driving_gaze = assess_driving_gaze(gaze, head_pose)
        completed_glance = self._glance_tracker.update(
            driving_gaze.gaze_status
        )
        if completed_glance is not None:
            self._glance_history.add(completed_glance)
        distraction = self._distraction_analyzer.update(
            self._glance_history,
            self._glance_tracker.active_start_time,
            driving_gaze.gaze_status,
        )

        drowsiness = self._process_drowsiness(
            face_status,
            face_landmarks,
            timestamp_ms,
        )
        phone = self._process_phone(frame)

        return EngineFrameOutput(
            timestamps=timestamps,
            face_status=face_status,
            gaze=driving_gaze,
            distraction=distraction,
            drowsiness=drowsiness,
            phone=phone,
            perclos_percent=drowsiness.perclos_percent,
        )

    def _process_face(self, frame: object, timestamp_ms: int) -> object | None:
        if self._face_provider is None:
            return None
        try:
            result = self._face_provider.process_frame(frame, timestamp_ms)
            if isinstance(result, FaceObservation):
                return result
            return face_observation_from_result(result, timestamp_ms)
        except (RuntimeError, ValueError, NotImplementedError) as exc:
            self.last_face_error = exc
            return None

    def _process_gaze(
        self,
        face_landmarks: tuple[object, ...] | list[object],
    ) -> GazeClassification | None:
        result = self._gaze_processor.update(face_landmarks)
        self.last_gaze_error = self._gaze_processor.last_error
        return result

    def _process_drowsiness(
        self,
        face_status: FaceFrameStatus,
        face_landmarks: tuple[object, ...] | list[object] | None,
        timestamp_ms: int,
    ) -> DrowsinessObservation:
        result = self._drowsiness_analyzer.update(
            face_status,
            face_landmarks,
            timestamp_ms,
        )
        self.last_drowsiness_error = self._drowsiness_analyzer.last_error
        return result

    def _process_phone(self, frame: object) -> PhoneObservation:
        if self._phone_provider is None:
            return PhoneObservation(PhoneFrameStatus.UNAVAILABLE)
        try:
            observation = self._phone_provider.process_frame(frame)
            if not isinstance(observation, PhoneObservation):
                raise ValueError(
                    "Phone provider must return PhoneObservation."
                )
            return observation
        except (RuntimeError, ValueError, NotImplementedError):
            return PhoneObservation(PhoneFrameStatus.UNAVAILABLE)


class _NoFaceResult:
    """Minimal result shape accepted by the head-pose estimator."""

    face_landmarks = None
    facial_transformation_matrixes = None


class _FaceResult:
    """Minimal result shape for head-pose estimator from FaceObservation."""

    def __init__(
        self,
        face_landmarks: list[object],
        facial_matrix: object | None,
    ) -> None:
        self.face_landmarks = [face_landmarks]
        self.facial_transformation_matrixes = (
            [facial_matrix] if facial_matrix is not None else None
        )
