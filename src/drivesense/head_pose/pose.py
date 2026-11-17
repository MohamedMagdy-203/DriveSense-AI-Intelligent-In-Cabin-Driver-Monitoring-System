"""Head pose estimation from MediaPipe facial transformation matrices."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from mediapipe.tasks.python.vision.face_landmarker import FaceLandmarkerResult
import numpy as np


class HeadPoseStatus(str, Enum):
    """Outcome of processing one Face Landmarker result."""

    OK = "OK"
    NO_FACE = "NO_FACE"
    NO_MATRIX = "NO_MATRIX"


@dataclass(frozen=True)
class HeadPoseEstimate:
    """Relative rotation-vector estimate for one detected face."""

    status: HeadPoseStatus
    x_deg: float | None = None
    y_deg: float | None = None
    z_deg: float | None = None
    magnitude_deg: float | None = None

    @property
    def rotation_vector_degrees(self) -> tuple[float, float, float] | None:
        if self.x_deg is None or self.y_deg is None or self.z_deg is None:
            return None
        return self.x_deg, self.y_deg, self.z_deg


def _normalized_rotation(matrix: np.ndarray) -> np.ndarray:
    if matrix.shape != (4, 4):
        raise ValueError(
            "Expected a 4x4 facial transformation matrix, "
            f"got {matrix.shape}."
        )
    if not np.isfinite(matrix).all():
        raise ValueError("Facial transformation matrix contains non-finite values.")
    rotation = matrix[:3, :3].astype(float)
    scale = float(np.mean(np.linalg.norm(rotation, axis=0)))
    if scale <= 0:
        raise ValueError("Facial transformation matrix has zero rotation scale.")
    return rotation / scale


def _rotation_vector(rotation: np.ndarray) -> np.ndarray:
    cosine = float(np.clip((np.trace(rotation) - 1) / 2, -1.0, 1.0))
    angle = math.acos(cosine)
    skew = np.array(
        [
            rotation[2, 1] - rotation[1, 2],
            rotation[0, 2] - rotation[2, 0],
            rotation[1, 0] - rotation[0, 1],
        ]
    )
    if angle < 1e-8:
        return skew / 2
    sine = math.sin(angle)
    if abs(sine) > 1e-8:
        return skew * (angle / (2 * sine))

    diagonal = np.diag(rotation)
    axis = np.sqrt(np.maximum((diagonal + 1) / 2, 0))
    largest = int(np.argmax(axis))
    if axis[largest] < 1e-8:
        raise ValueError("Could not extract a rotation axis.")
    for index in range(3):
        if index != largest:
            axis[index] = (
                rotation[largest, index] + rotation[index, largest]
            ) / (4 * axis[largest])
    return axis * angle


class HeadPoseEstimator:
    """Estimate relative rotation vectors from Face Landmarker results."""

    def __init__(self) -> None:
        self._neutral_rotation: np.ndarray | None = None

    @property
    def is_calibrated(self) -> bool:
        return self._neutral_rotation is not None

    def reset_neutral(self) -> None:
        """Clear the reference so the next valid matrix becomes Neutral."""
        self._neutral_rotation = None

    def update(
        self,
        result: FaceLandmarkerResult,
        face_index: int = 0,
    ) -> HeadPoseEstimate:
        """Process one Face Landmarker result.

        Missing faces and missing matrices return explicit statuses and do not
        change the current Neutral reference.
        """
        face_landmarks = getattr(result, "face_landmarks", None)
        if not face_landmarks or face_index >= len(face_landmarks):
            return HeadPoseEstimate(HeadPoseStatus.NO_FACE)

        matrices = getattr(result, "facial_transformation_matrixes", None)
        if not matrices or face_index >= len(matrices):
            return HeadPoseEstimate(HeadPoseStatus.NO_MATRIX)

        matrix = np.asarray(matrices[face_index], dtype=float)
        rotation = _normalized_rotation(matrix)
        if self._neutral_rotation is None:
            self._neutral_rotation = rotation

        relative_rotation = self._neutral_rotation.T @ rotation
        vector_degrees = np.degrees(_rotation_vector(relative_rotation))
        magnitude_degrees = float(np.linalg.norm(vector_degrees))
        return HeadPoseEstimate(
            status=HeadPoseStatus.OK,
            x_deg=float(vector_degrees[0]),
            y_deg=float(vector_degrees[1]),
            z_deg=float(vector_degrees[2]),
            magnitude_deg=magnitude_degrees,
        )
