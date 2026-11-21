"""Validated application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.yaml"


@dataclass(frozen=True)
class CameraConfig:
    index: int
    width: int
    height: int
    window_name: str


@dataclass(frozen=True)
class MediaPipeConfig:
    model_path: Path
    delegate: str
    min_face_detection_confidence: float
    min_face_presence_confidence: float
    min_tracking_confidence: float


@dataclass(frozen=True)
class TemporalConfig:
    head_pose_window_seconds: float
    long_glance_seconds: float
    glance_window_seconds: float
    reengagement_seconds: float
    cumulative_glance_seconds: float


@dataclass(frozen=True)
class DrowsinessConfig:
    perclos_window_seconds: float
    closure_score_threshold: float
    blink_exclusion_seconds: float
    prolonged_closure_test_seconds: float
    open_openness_baseline: float
    closed_openness_baseline: float


@dataclass(frozen=True)
class AppConfig:
    camera: CameraConfig
    mediapipe: MediaPipeConfig
    temporal: TemporalConfig
    drowsiness: DrowsinessConfig


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"Configuration section '{name}' must be a mapping.")
    return value


def _positive_number(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive number.")
    return float(value)


def _confidence(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a number between 0 and 1.")
    result = float(value)
    if not 0 <= result <= 1:
        raise ValueError(f"{name} must be between 0 and 1.")
    return result


def _number(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a number.")
    return float(value)


def _nonnegative_number(value: Any, name: str) -> float:
    result = _number(value, name)
    if result < 0:
        raise ValueError(f"{name} must be non-negative.")
    return result


def load_config(path: Path | None = None) -> AppConfig:
    """Load and validate application settings from YAML."""
    config_path = path or DEFAULT_CONFIG_PATH
    with config_path.open(encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file) or {}
    if not isinstance(raw, dict):
        raise ValueError("The root configuration value must be a mapping.")

    camera = _section(raw, "camera")
    mediapipe = _section(raw, "mediapipe")
    temporal = _section(raw, "temporal")
    drowsiness = _section(raw, "drowsiness")
    width = camera.get("width")
    height = camera.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        raise ValueError("camera.width must be a positive integer.")
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        raise ValueError("camera.height must be a positive integer.")
    index = camera.get("index")
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise ValueError("camera.index must be a non-negative integer.")
    window_name = camera.get("window_name")
    if not isinstance(window_name, str) or not window_name:
        raise ValueError("camera.window_name must be a non-empty string.")

    model_path_value = mediapipe.get("model_path")
    if not isinstance(model_path_value, str) or not model_path_value:
        raise ValueError("mediapipe.model_path must be a non-empty string.")
    delegate = mediapipe.get("delegate")
    if delegate != "CPU":
        raise ValueError("mediapipe.delegate must be 'CPU'.")

    open_openness_baseline = _number(
        drowsiness.get("open_openness_baseline"),
        "drowsiness.open_openness_baseline",
    )
    closed_openness_baseline = _number(
        drowsiness.get("closed_openness_baseline"),
        "drowsiness.closed_openness_baseline",
    )
    if open_openness_baseline <= closed_openness_baseline:
        raise ValueError(
            "drowsiness.open_openness_baseline must be greater than "
            "drowsiness.closed_openness_baseline"
        )

    return AppConfig(
        camera=CameraConfig(index, width, height, window_name),
        mediapipe=MediaPipeConfig(
            model_path=PROJECT_ROOT / model_path_value,
            delegate=delegate,
            min_face_detection_confidence=_confidence(
                mediapipe.get("min_face_detection_confidence"),
                "mediapipe.min_face_detection_confidence",
            ),
            min_face_presence_confidence=_confidence(
                mediapipe.get("min_face_presence_confidence"),
                "mediapipe.min_face_presence_confidence",
            ),
            min_tracking_confidence=_confidence(
                mediapipe.get("min_tracking_confidence"),
                "mediapipe.min_tracking_confidence",
            ),
        ),
        temporal=TemporalConfig(
            head_pose_window_seconds=_positive_number(
                temporal.get("head_pose_window_seconds"),
                "temporal.head_pose_window_seconds",
            ),
            long_glance_seconds=_positive_number(
                temporal.get("long_glance_seconds"),
                "temporal.long_glance_seconds",
            ),
            glance_window_seconds=_positive_number(
                temporal.get("glance_window_seconds"),
                "temporal.glance_window_seconds",
            ),
            reengagement_seconds=_positive_number(
                temporal.get("reengagement_seconds"),
                "temporal.reengagement_seconds",
            ),
            cumulative_glance_seconds=_positive_number(
                temporal.get("cumulative_glance_seconds"),
                "temporal.cumulative_glance_seconds",
            ),
        ),
        drowsiness=DrowsinessConfig(
            perclos_window_seconds=_positive_number(
                drowsiness.get("perclos_window_seconds"),
                "drowsiness.perclos_window_seconds",
            ),
            closure_score_threshold=_confidence(
                drowsiness.get("closure_score_threshold"),
                "drowsiness.closure_score_threshold",
            ),
            blink_exclusion_seconds=_nonnegative_number(
                drowsiness.get("blink_exclusion_seconds"),
                "drowsiness.blink_exclusion_seconds",
            ),
            prolonged_closure_test_seconds=_positive_number(
                drowsiness.get("prolonged_closure_test_seconds"),
                "drowsiness.prolonged_closure_test_seconds",
            ),
            open_openness_baseline=open_openness_baseline,
            closed_openness_baseline=closed_openness_baseline,
        ),
    )