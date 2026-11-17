import numpy as np
import pytest

from drivesense.head_pose.pose import (
    HeadPoseEstimate,
    HeadPoseStatus,
    _normalized_rotation,
)
from drivesense.head_pose.temporal import HeadPoseTemporalAnalyzer


def test_uniform_scale_is_removed_from_rotation_matrix() -> None:
    matrix = np.eye(4) * 2.0
    matrix[3, 3] = 1.0

    result = _normalized_rotation(matrix)

    assert result == pytest.approx(np.eye(3))


def test_temporal_history_keeps_only_valid_estimates(monkeypatch) -> None:
    timestamps = iter((10.0, 10.5, 11.0, 13.0))
    monkeypatch.setattr(
        "drivesense.head_pose.temporal.time.monotonic",
        lambda: next(timestamps),
    )
    analyzer = HeadPoseTemporalAnalyzer(window_seconds=2.0)
    valid = HeadPoseEstimate(HeadPoseStatus.OK, 1.0, 2.0, 3.0, 4.0)

    analyzer.update(valid)
    analyzer.update(HeadPoseEstimate(HeadPoseStatus.NO_FACE))
    state = analyzer.update(valid)

    assert state.current_estimate is valid
    assert len(state.history) == 1
    assert state.history[0].timestamp_monotonic == 13.0
