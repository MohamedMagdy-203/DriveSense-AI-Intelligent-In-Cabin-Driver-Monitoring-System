"""Gaze-direction classification using per-eye calibration ranges."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from drivesense.visual_distraction.gaze.calibration import EyeCalibration
from drivesense.visual_distraction.gaze.geometry import (
    NormalizedIrisPosition,
    normalized_iris_positions,
)
from typing import Mapping


class GazeDirection(str, Enum):
    CENTER = "CENTER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP = "UP"
    DOWN = "DOWN"


@dataclass(frozen=True)
class EyeGazeClassification:
    """Classification and normalized deviations for one eye."""

    eye: str
    horizontal: GazeDirection
    vertical: GazeDirection
    horizontal_deviation: float
    vertical_deviation: float


@dataclass(frozen=True)
class GazeClassification:
    """Combined gaze classification for both eyes."""

    direction: GazeDirection
    eyes: tuple[EyeGazeClassification, ...]


def _signed_deviation(
    value: float,
    neutral: float,
    minimum: float,
    maximum: float,
) -> float:
    if minimum > neutral or neutral > maximum:
        raise ValueError("Calibration neutral must lie within its observed range.")
    if value < minimum:
        span = neutral - minimum
        return (value - neutral) / span if span > 0 else -1.0
    if value > maximum:
        span = maximum - neutral
        return (value - neutral) / span if span > 0 else 1.0
    return 0.0


def _horizontal_direction(deviation: float) -> GazeDirection:
    if deviation < 0:
        return GazeDirection.LEFT
    if deviation > 0:
        return GazeDirection.RIGHT
    return GazeDirection.CENTER


def _vertical_direction(deviation: float) -> GazeDirection:
    if deviation < 0:
        return GazeDirection.UP
    if deviation > 0:
        return GazeDirection.DOWN
    return GazeDirection.CENTER


def classify_eye_gaze(
    position: NormalizedIrisPosition,
    calibration: EyeCalibration,
    horizontal_sign: int = 1,
) -> EyeGazeClassification:
    """Classify one eye outside its calibrated natural-gaze band.

    `horizontal_sign=-1` reverses the semantic horizontal direction for an
    eye whose local corner ordering is opposite to the chosen convention.
    """
    if horizontal_sign not in (-1, 1):
        raise ValueError("horizontal_sign must be either -1 or 1.")
    if position.eye != calibration.eye:
        raise ValueError("Position and calibration must refer to the same eye.")
    horizontal_deviation = horizontal_sign * _signed_deviation(
        position.horizontal,
        calibration.neutral_horizontal,
        calibration.horizontal_min,
        calibration.horizontal_max,
    )
    vertical_deviation = _signed_deviation(
        position.vertical,
        calibration.neutral_vertical,
        calibration.vertical_min,
        calibration.vertical_max,
    )
    return EyeGazeClassification(
        eye=position.eye,
        horizontal=_horizontal_direction(horizontal_deviation),
        vertical=_vertical_direction(vertical_deviation),
        horizontal_deviation=horizontal_deviation,
        vertical_deviation=vertical_deviation,
    )


def classify_gaze(
    positions: dict[str, NormalizedIrisPosition],
    calibrations: dict[str, EyeCalibration],
    horizontal_signs: dict[str, int] | None = None,
) -> GazeClassification:
    """Combine per-eye classifications into one primary direction.

    Horizontal and vertical results are retained per eye. The combined
    direction is the strongest non-center axis; if both axes are centered, it
    is `CENTER`.
    """
    horizontal_signs = horizontal_signs or {}
    eye_results = tuple(
        classify_eye_gaze(
            positions[eye],
            calibrations[eye],
            horizontal_signs.get(eye, 1),
        )
        for eye in ("right_eye", "left_eye")
        if eye in positions and eye in calibrations
    )
    if not eye_results:
        raise ValueError("At least one calibrated eye position is required.")

    horizontal_score = sum(
        result.horizontal_deviation for result in eye_results
    ) / len(eye_results)
    vertical_score = sum(
        result.vertical_deviation for result in eye_results
    ) / len(eye_results)
    if abs(horizontal_score) >= abs(vertical_score):
        direction = _horizontal_direction(horizontal_score)
    else:
        direction = _vertical_direction(vertical_score)
    return GazeClassification(direction=direction, eyes=eye_results)


class GazeProcessor:
    """Turn first-face landmarks into one calibrated gaze classification."""

    def __init__(
        self,
        calibrations: Mapping[str, EyeCalibration] | None = None,
        horizontal_signs: Mapping[str, int] | None = None,
    ) -> None:
        self._calibrations = dict(calibrations or {})
        self._horizontal_signs = dict(horizontal_signs or {})
        self.last_error: Exception | None = None

    def update(
        self,
        face_landmarks: tuple[object, ...] | list[object],
    ) -> GazeClassification | None:
        if set(self._calibrations) != {"right_eye", "left_eye"}:
            return None
        try:
            positions = normalized_iris_positions(list(face_landmarks))
            result = classify_gaze(
                positions,
                self._calibrations,
                self._horizontal_signs,
            )
            self.last_error = None
            return result
        except (IndexError, KeyError, ValueError) as exc:
            self.last_error = exc
            return None
