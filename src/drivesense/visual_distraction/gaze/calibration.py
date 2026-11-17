"""Calibration statistics for person-specific geometric eye gaze."""

from __future__ import annotations

from dataclasses import dataclass
import statistics

from drivesense.visual_distraction.gaze.geometry import NormalizedIrisPosition


@dataclass(frozen=True)
class EyeCalibration:
    """Neutral reference and observed ranges for one eye."""

    eye: str
    neutral_horizontal: float
    neutral_vertical: float
    horizontal_min: float
    horizontal_max: float
    vertical_min: float
    vertical_max: float
    sample_count: int


def calibrate_eye(
    positions: list[NormalizedIrisPosition],
) -> EyeCalibration:
    """Calculate calibration statistics without defining gaze classes."""
    if not positions:
        raise ValueError("At least one eye-position sample is required.")
    eye_names = {position.eye for position in positions}
    if len(eye_names) != 1:
        raise ValueError("All calibration samples must belong to one eye.")
    horizontal = [position.horizontal for position in positions]
    vertical = [position.vertical for position in positions]
    return EyeCalibration(
        eye=positions[0].eye,
        neutral_horizontal=statistics.fmean(horizontal),
        neutral_vertical=statistics.fmean(vertical),
        horizontal_min=min(horizontal),
        horizontal_max=max(horizontal),
        vertical_min=min(vertical),
        vertical_max=max(vertical),
        sample_count=len(positions),
    )


def calibrate_gaze(
    samples: list[dict[str, NormalizedIrisPosition]],
) -> dict[str, EyeCalibration]:
    """Calculate independent calibration statistics for both eyes."""
    if not samples:
        raise ValueError("At least one gaze sample is required.")
    return {
        eye: calibrate_eye(
            [sample[eye] for sample in samples if eye in sample]
        )
        for eye in ("right_eye", "left_eye")
    }
