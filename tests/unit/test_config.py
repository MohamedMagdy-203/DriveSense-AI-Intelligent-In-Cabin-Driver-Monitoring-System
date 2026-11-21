from pathlib import Path

import pytest

from drivesense.config import load_config


def test_default_config_preserves_runtime_defaults() -> None:
    config = load_config()

    assert config.camera.width == 640
    assert config.camera.height == 480
    assert config.mediapipe.delegate == "CPU"
    assert config.temporal.head_pose_window_seconds == 2.0
    assert config.temporal.long_glance_seconds == 3.0
    assert config.temporal.cumulative_glance_seconds == 10.0
    assert config.temporal.glance_window_seconds == 30.0
    assert config.drowsiness.perclos_window_seconds == 60.0
    assert config.drowsiness.prolonged_closure_test_seconds == 4.0


def test_config_rejects_non_cpu_delegate(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        """
camera:
  index: 0
  width: 640
  height: 480
  window_name: test
mediapipe:
  model_path: models/face_landmarker.task
  delegate: GPU
  min_face_detection_confidence: 0.5
  min_face_presence_confidence: 0.5
  min_tracking_confidence: 0.5
temporal:
  head_pose_window_seconds: 2
  long_glance_seconds: 3
  glance_window_seconds: 30
  reengagement_seconds: 2
  cumulative_glance_seconds: 10
drowsiness:
  perclos_window_seconds: 60
  closure_score_threshold: 0.8
  blink_exclusion_seconds: 0.2
  prolonged_closure_test_seconds: 4
  open_openness_baseline: 0.3298
  closed_openness_baseline: 0.0736
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="delegate"):
        load_config(config_path)
