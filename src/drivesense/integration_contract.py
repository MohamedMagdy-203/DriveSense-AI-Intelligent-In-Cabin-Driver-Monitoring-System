"""Typed integration contract for the future DriveSense engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from drivesense.head_pose.pose import HeadPoseEstimate
from drivesense.visual_distraction.assessment import (
    DrivingGazeAssessment,
)
from drivesense.visual_distraction.gaze.classification import GazeClassification
from drivesense.visual_distraction.temporal import DistractionAssessment


class FaceFrameStatus(str, Enum):
    """Availability of MediaPipe output for one frame."""

    AVAILABLE = "AVAILABLE"
    NO_FACE = "NO_FACE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class FaceObservation:
    """Normalized first-face output independent of MediaPipe result objects."""

    status: FaceFrameStatus
    landmarks: tuple[object, ...] = ()
    facial_matrix: object | None = None
    timestamp_ms: int | None = None

    def __post_init__(self) -> None:
        if self.status is FaceFrameStatus.AVAILABLE:
            if not self.landmarks:
                raise ValueError("AVAILABLE face observation requires landmarks.")
        elif self.landmarks:
            raise ValueError("Landmarks require AVAILABLE face status.")
        if self.timestamp_ms is not None and self.timestamp_ms < 0:
            raise ValueError("Face timestamp_ms must be non-negative.")


@dataclass(frozen=True)
class FrameTimestamps:
    """Separate timestamp domains used by the existing implementations."""

    media_pipe_ms: int
    monotonic_seconds: float

    def __post_init__(self) -> None:
        if self.media_pipe_ms < 0:
            raise ValueError("media_pipe_ms must be non-negative.")
        if self.monotonic_seconds < 0:
            raise ValueError("monotonic_seconds must be non-negative.")


class PhoneFrameStatus(str, Enum):
    """Availability of the optional phone detector for one frame."""

    DETECTED = "DETECTED"
    NOT_DETECTED = "NOT_DETECTED"
    UNAVAILABLE = "UNAVAILABLE"


class PhoneResultFreshness(str, Enum):
    """Freshness metadata for cached or asynchronous phone results."""

    UNKNOWN = "UNKNOWN"
    FRESH = "FRESH"
    CACHED = "CACHED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class DrowsinessFrameStatus(str, Enum):
    """Availability of drowsiness signals for one frame."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PROLONGED_CLOSURE_TEST = "PROLONGED_CLOSURE_TEST"
    NO_FACE = "NO_FACE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class DrowsinessObservation:
    """Frame-level drowsiness output without alert decisions."""

    status: DrowsinessFrameStatus
    perclos_percent: float | None = None
    closure_score: float | None = None

    def __post_init__(self) -> None:
        if self.perclos_percent is not None:
            if not 0.0 <= self.perclos_percent <= 100.0:
                raise ValueError("PERCLOS percentage must be between 0 and 100.")
        if self.closure_score is not None:
            if not 0.0 <= self.closure_score <= 1.0:
                raise ValueError("Closure score must be between 0 and 1.")


@dataclass(frozen=True)
class PhoneDetection:
    """One normalized phone-detection box."""

    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Phone confidence must be between 0 and 1.")
        for coordinate in (self.x1, self.y1, self.x2, self.y2):
            if not 0.0 <= coordinate <= 1.0:
                raise ValueError("Phone coordinates must be normalized.")
        if self.x2 < self.x1 or self.y2 < self.y1:
            raise ValueError("Phone box coordinates must be ordered.")


@dataclass(frozen=True)
class PhoneObservation:
    """Frame-level output from the phone detector."""

    status: PhoneFrameStatus
    detections: tuple[PhoneDetection, ...] = ()
    timestamp_monotonic: float | None = None
    freshness: PhoneResultFreshness = PhoneResultFreshness.UNKNOWN

    def __post_init__(self) -> None:
        if self.status is PhoneFrameStatus.DETECTED and not self.detections:
            raise ValueError("DETECTED status requires at least one detection.")
        if self.status is not PhoneFrameStatus.DETECTED and self.detections:
            raise ValueError("A phone detection list requires DETECTED status.")
        if self.timestamp_monotonic is not None and self.timestamp_monotonic < 0:
            raise ValueError("Phone observation timestamp must be non-negative.")
        if self.status is PhoneFrameStatus.UNAVAILABLE:
            if self.freshness not in (
                PhoneResultFreshness.UNKNOWN,
                PhoneResultFreshness.UNAVAILABLE,
            ):
                raise ValueError(
                    "UNAVAILABLE phone status requires unavailable freshness."
                )

    @property
    def is_stale(self) -> bool:
        return self.freshness is PhoneResultFreshness.STALE


@dataclass(frozen=True)
class EngineFrameInput:
    """All signals collected or classified for one webcam frame."""

    timestamps: FrameTimestamps
    face_landmarks: tuple[object, ...] | None = None
    facial_matrix: object | None = None
    gaze: GazeClassification | None = None
    head_pose: HeadPoseEstimate | None = None
    phone: PhoneObservation = PhoneObservation(
        PhoneFrameStatus.UNAVAILABLE
    )

    def __post_init__(self) -> None:
        if not isinstance(self.timestamps, FrameTimestamps):
            raise ValueError("timestamps must be a FrameTimestamps instance.")


@dataclass(frozen=True)
class EngineFrameOutput:
    """Normalized frame-level result produced by the integration engine."""

    timestamps: FrameTimestamps
    face_status: FaceFrameStatus
    gaze: DrivingGazeAssessment
    distraction: DistractionAssessment
    drowsiness: DrowsinessObservation
    phone: PhoneObservation
    perclos_percent: float | None = None


class FaceSignalProvider(Protocol):
    """Adapter contract for a MediaPipe Face Landmarker runtime."""

    def process_frame(
        self,
        frame: object,
        timestamp_ms: int,
    ) -> object:
        """Return one raw Face Landmarker result for an increasing timestamp."""
        ...


class PhoneSignalProvider(Protocol):
    """Adapter contract for an object detector such as YOLO."""

    def process_frame(
        self,
        frame: object,
    ) -> PhoneObservation:
        """Return normalized phone detections for the frame."""
        ...


__all__ = [
    "EngineFrameInput",
    "EngineFrameOutput",
    "FaceObservation",
    "DrowsinessFrameStatus",
    "DrowsinessObservation",
    "FaceFrameStatus",
    "FaceSignalProvider",
    "FrameTimestamps",
    "PhoneDetection",
    "PhoneFrameStatus",
    "PhoneObservation",
    "PhoneResultFreshness",
    "PhoneSignalProvider",
]
