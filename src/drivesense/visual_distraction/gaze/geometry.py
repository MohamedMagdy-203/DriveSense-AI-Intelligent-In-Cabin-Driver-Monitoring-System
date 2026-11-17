"""Geometric iris-position estimation from Face Landmarker landmarks."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol


class Landmark(Protocol):
    x: float
    y: float

IRIS_POINTS = {
    "right_eye": (468, 469, 470, 471, 472),
    "left_eye": (473, 474, 475, 476, 477),
}
EYE_GEOMETRY = {
    "right_eye": {
        "corners": (33, 133),
        "upper": (160, 158),
        "lower": (153, 144),
    },
    "left_eye": {
        "corners": (362, 263),
        "upper": (385, 387),
        "lower": (373, 380),
    },
}


@dataclass(frozen=True)
class NormalizedIrisPosition:
    """Iris position in the local eye coordinate system."""

    eye: str
    iris_center_x: float
    iris_center_y: float
    horizontal: float
    vertical: float


def _mean_point(
    face_landmarks: list[Landmark],
    indices: tuple[int, ...],
) -> tuple[float, float]:
    points = [face_landmarks[index] for index in indices]
    return (
        sum(point.x for point in points) / len(points),
        sum(point.y for point in points) / len(points),
    )


def _subtract(first: tuple[float, float], second: tuple[float, float]) -> tuple[float, float]:
    return first[0] - second[0], first[1] - second[1]


def _dot(first: tuple[float, float], second: tuple[float, float]) -> float:
    return first[0] * second[0] + first[1] * second[1]


def _projected_position(
    point: tuple[float, float],
    origin: tuple[float, float],
    endpoint: tuple[float, float],
) -> float:
    axis = _subtract(endpoint, origin)
    length_squared = _dot(axis, axis)
    if length_squared == 0:
        raise ValueError("Eye landmarks define a zero-length axis.")
    return _dot(_subtract(point, origin), axis) / length_squared


def normalized_iris_position(
    face_landmarks: list[Landmark],
    eye: str,
) -> NormalizedIrisPosition:
    """Return the iris center and normalized horizontal/vertical position.

    Horizontal position is projected from the first eye corner to the second
    corner. Vertical position is projected from the upper-eyelid midpoint to
    the lower-eyelid midpoint. Both values are approximately 0 at the first
    axis endpoint and 1 at the second.
    """
    if eye not in IRIS_POINTS or eye not in EYE_GEOMETRY:
        raise ValueError(f"Unknown eye: {eye}")

    geometry = EYE_GEOMETRY[eye]
    iris_center = _mean_point(face_landmarks, IRIS_POINTS[eye])
    corners = [
        face_landmarks[index] for index in geometry["corners"]
    ]
    upper = _mean_point(face_landmarks, geometry["upper"])
    lower = _mean_point(face_landmarks, geometry["lower"])
    corner_start = (corners[0].x, corners[0].y)
    corner_end = (corners[1].x, corners[1].y)
    horizontal = _projected_position(iris_center, corner_start, corner_end)
    vertical = _projected_position(iris_center, upper, lower)
    return NormalizedIrisPosition(
        eye=eye,
        iris_center_x=iris_center[0],
        iris_center_y=iris_center[1],
        horizontal=horizontal,
        vertical=vertical,
    )


def normalized_iris_positions(
    face_landmarks: list[Landmark],
) -> dict[str, NormalizedIrisPosition]:
    """Calculate normalized iris positions for both eyes."""
    return {
        eye: normalized_iris_position(face_landmarks, eye)
        for eye in IRIS_POINTS
    }
