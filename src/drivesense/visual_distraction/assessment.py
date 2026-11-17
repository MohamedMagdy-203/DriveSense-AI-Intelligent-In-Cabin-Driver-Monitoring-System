"""Gaze assessment output structures and camera-reference evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from drivesense.visual_distraction.gaze.classification import (
    GazeClassification,
    GazeDirection,
)
from drivesense.head_pose.pose import HeadPoseEstimate, HeadPoseStatus


class GazeAssessmentStatus(str, Enum):
    """Assessment state reserved for the eye-gaze signal."""

    UNDETERMINED = "UNDETERMINED"
    ON_REFERENCE = "ON_REFERENCE"
    OFF_REFERENCE = "OFF_REFERENCE"
    UNAVAILABLE = "UNAVAILABLE"


class HeadAssessmentStatus(str, Enum):
    """Assessment state reserved for the supporting head-pose signal."""

    UNDETERMINED = "UNDETERMINED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class DrivingGazeStatus(str, Enum):
    """Overall assessment state before signal-fusion rules are defined."""

    UNDETERMINED = "UNDETERMINED"
    ATTENTIVE = "ATTENTIVE"
    DISTRACTED = "DISTRACTED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class DrivingGazeAssessment:
    """Structured output for one driving-gaze assessment."""

    status: DrivingGazeStatus = DrivingGazeStatus.UNDETERMINED
    gaze_status: GazeAssessmentStatus = GazeAssessmentStatus.UNDETERMINED
    head_status: HeadAssessmentStatus = HeadAssessmentStatus.UNDETERMINED


def assess_gaze(
    gaze_classification: GazeClassification | None,
) -> GazeAssessmentStatus:
    """Assess gaze direction relative to the camera reference.

    This only maps the existing gaze classification to a status. It does not
    claim that the camera reference represents the road or use timing rules.
    """
    if gaze_classification is None or not gaze_classification.eyes:
        return GazeAssessmentStatus.UNAVAILABLE
    if gaze_classification.direction is GazeDirection.CENTER:
        return GazeAssessmentStatus.ON_REFERENCE
    return GazeAssessmentStatus.OFF_REFERENCE


def assess_driving_gaze(
    gaze_classification: GazeClassification | None,
    head_pose: HeadPoseEstimate | None = None,
) -> DrivingGazeAssessment:
    """Create an assessment using the current gaze/head fusion rules.

    ``ATTENTIVE`` is limited to gaze being on the camera reference while a
    valid head-pose estimate is available. All other available combinations
    remain unresolved until temporal and contextual analysis is added.
    """
    gaze_status = assess_gaze(gaze_classification)
    head_status = assess_head_pose(head_pose)
    if (
        gaze_status is GazeAssessmentStatus.ON_REFERENCE
        and head_status is HeadAssessmentStatus.AVAILABLE
    ):
        overall_status = DrivingGazeStatus.ATTENTIVE
    elif (
        gaze_status is GazeAssessmentStatus.UNAVAILABLE
        and head_status is HeadAssessmentStatus.UNAVAILABLE
    ):
        overall_status = DrivingGazeStatus.UNAVAILABLE
    else:
        overall_status = DrivingGazeStatus.UNDETERMINED

    return DrivingGazeAssessment(
        status=overall_status,
        gaze_status=gaze_status,
        head_status=head_status,
    )


def assess_head_pose(
    head_pose: HeadPoseEstimate | None,
) -> HeadAssessmentStatus:
    """Assess whether a usable head-pose estimate is available."""
    if head_pose is None or head_pose.status is not HeadPoseStatus.OK:
        return HeadAssessmentStatus.UNAVAILABLE

    rotation_vector = head_pose.rotation_vector_degrees
    if rotation_vector is None or not all(
        math.isfinite(value) for value in rotation_vector
    ):
        return HeadAssessmentStatus.UNAVAILABLE
    return HeadAssessmentStatus.AVAILABLE
