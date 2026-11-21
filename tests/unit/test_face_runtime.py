from types import SimpleNamespace

import pytest

from drivesense.face.runtime import face_observation_from_result
from drivesense.integration_contract import FaceFrameStatus


def test_face_observation_conversion_returns_available_with_first_face() -> None:
    landmarks = [
        SimpleNamespace(x=0.5, y=0.5, z=0.0)
        for _ in range(478)
    ]
    matrix = [[1.0] * 4 for _ in range(4)]
    result = SimpleNamespace(
        face_landmarks=[landmarks, []],
        facial_transformation_matrixes=[matrix, None],
    )

    observation = face_observation_from_result(result, 125)

    assert observation.status is FaceFrameStatus.AVAILABLE
    assert len(observation.landmarks) == 478
    assert observation.facial_matrix is matrix
    assert observation.timestamp_ms == 125


def test_face_observation_conversion_returns_no_face() -> None:
    observation = face_observation_from_result(
        SimpleNamespace(
            face_landmarks=[],
            facial_transformation_matrixes=None,
        ),
        125,
    )

    assert observation.status is FaceFrameStatus.NO_FACE
    assert observation.landmarks == ()


def test_face_observation_conversion_rejects_invalid_landmark_count() -> None:
    result = SimpleNamespace(
        face_landmarks=[[SimpleNamespace(x=0.5, y=0.5, z=0.0)] * 100],
        facial_transformation_matrixes=None,
    )

    with pytest.raises(ValueError, match="478"):
        face_observation_from_result(result, 125)
