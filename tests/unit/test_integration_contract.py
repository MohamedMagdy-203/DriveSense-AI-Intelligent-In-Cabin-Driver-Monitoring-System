import pytest

from drivesense.integration_contract import (
    FrameTimestamps,
    FaceFrameStatus,
    FaceObservation,
    PhoneDetection,
    PhoneFrameStatus,
    PhoneObservation,
    PhoneResultFreshness,
)


def test_phone_detection_accepts_normalized_box() -> None:
    detection = PhoneDetection(
        confidence=0.75,
        x1=0.1,
        y1=0.2,
        x2=0.4,
        y2=0.5,
    )
    observation = PhoneObservation(
        PhoneFrameStatus.DETECTED,
        (detection,),
    )

    assert observation.status is PhoneFrameStatus.DETECTED
    assert observation.detections == (detection,)


@pytest.mark.parametrize(
    "confidence",
    [-0.01, 1.01],
)
def test_phone_detection_rejects_invalid_confidence(confidence: float) -> None:
    with pytest.raises(ValueError, match="confidence"):
        PhoneDetection(confidence, 0.1, 0.1, 0.2, 0.2)


def test_detected_status_requires_detection() -> None:
    with pytest.raises(ValueError, match="requires at least one"):
        PhoneObservation(PhoneFrameStatus.DETECTED)


def test_non_detected_status_rejects_detection_list() -> None:
    detection = PhoneDetection(0.8, 0.1, 0.1, 0.2, 0.2)

    with pytest.raises(ValueError, match="requires DETECTED"):
        PhoneObservation(PhoneFrameStatus.NOT_DETECTED, (detection,))


def test_frame_timestamps_keep_media_and_monotonic_domains_separate() -> None:
    timestamps = FrameTimestamps(
        media_pipe_ms=1250,
        monotonic_seconds=12.5,
    )

    assert timestamps.media_pipe_ms == 1250
    assert timestamps.monotonic_seconds == 12.5


@pytest.mark.parametrize(
    ("media_pipe_ms", "monotonic_seconds"),
    [(-1, 12.5), (1250, -1.0)],
)
def test_frame_timestamps_reject_negative_values(
    media_pipe_ms: int,
    monotonic_seconds: float,
) -> None:
    with pytest.raises(ValueError):
        FrameTimestamps(media_pipe_ms, monotonic_seconds)


def test_phone_observation_accepts_stale_detection_metadata() -> None:
    detection = PhoneDetection(0.8, 0.1, 0.1, 0.2, 0.2)

    observation = PhoneObservation(
        PhoneFrameStatus.DETECTED,
        (detection,),
        timestamp_monotonic=10.0,
        freshness=PhoneResultFreshness.STALE,
    )

    assert observation.is_stale


def test_phone_observation_rejects_negative_timestamp() -> None:
    with pytest.raises(ValueError, match="timestamp"):
        PhoneObservation(
            PhoneFrameStatus.NOT_DETECTED,
            timestamp_monotonic=-0.1,
        )


def test_phone_observation_rejects_inconsistent_unavailable_freshness() -> None:
    with pytest.raises(ValueError, match="unavailable freshness"):
        PhoneObservation(
            PhoneFrameStatus.UNAVAILABLE,
            freshness=PhoneResultFreshness.FRESH,
        )


def test_face_observation_requires_landmarks_when_available() -> None:
    with pytest.raises(ValueError, match="requires landmarks"):
        FaceObservation(FaceFrameStatus.AVAILABLE)


def test_face_observation_accepts_no_face_without_landmarks() -> None:
    observation = FaceObservation(FaceFrameStatus.NO_FACE)

    assert observation.status is FaceFrameStatus.NO_FACE
    assert observation.landmarks == ()
