from types import SimpleNamespace

import pytest

from drivesense.visual_distraction.gaze.calibration import calibrate_eye
from drivesense.visual_distraction.gaze.classification import (
    GazeDirection,
    classify_eye_gaze,
)
from drivesense.visual_distraction.gaze.geometry import (
    NormalizedIrisPosition,
    normalized_iris_position,
)


def test_normalized_iris_position_uses_eye_axes() -> None:
    landmarks = [SimpleNamespace(x=0.0, y=0.0) for _ in range(478)]
    for index, point in {
        33: (0.0, 0.5),
        133: (1.0, 0.5),
        160: (0.5, 0.0),
        158: (0.5, 0.0),
        153: (0.5, 1.0),
        144: (0.5, 1.0),
        468: (0.5, 0.5),
        469: (0.5, 0.5),
        470: (0.5, 0.5),
        471: (0.5, 0.5),
        472: (0.5, 0.5),
    }.items():
        landmarks[index] = SimpleNamespace(x=point[0], y=point[1])

    result = normalized_iris_position(landmarks, "right_eye")

    assert result.horizontal == pytest.approx(0.5)
    assert result.vertical == pytest.approx(0.5)


def test_gaze_classification_preserves_direction_and_sign() -> None:
    calibration = calibrate_eye(
        [
            NormalizedIrisPosition("right_eye", 0.5, 0.5, 0.4, 0.5),
            NormalizedIrisPosition("right_eye", 0.5, 0.5, 0.6, 0.5),
        ]
    )
    position = NormalizedIrisPosition("right_eye", 0.2, 0.5, 0.3, 0.5)

    result = classify_eye_gaze(position, calibration)

    assert result.horizontal is GazeDirection.LEFT
