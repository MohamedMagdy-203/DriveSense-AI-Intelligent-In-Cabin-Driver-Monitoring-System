from types import SimpleNamespace

import numpy as np
import pytest

from drivesense.engine import DriverMonitoringEngine
from drivesense.integration_contract import (
    DrowsinessFrameStatus,
    FaceFrameStatus,
    PhoneDetection,
    PhoneFrameStatus,
    PhoneObservation,
)
from drivesense.config import DrowsinessConfig
from drivesense.visual_distraction.gaze.calibration import EyeCalibration


class FakeFaceProvider:
    def __init__(self, result: object | None) -> None:
        self.result = result
        self.calls: list[tuple[object, int]] = []

    def process_frame(self, frame: object, timestamp_ms: int) -> object:
        self.calls.append((frame, timestamp_ms))
        if isinstance(self.result, RuntimeError):
            raise self.result
        if self.result is None:
            raise RuntimeError("Face provider unavailable")
        return self.result


class FakePhoneProvider:
    def __init__(self, observation: PhoneObservation) -> None:
        self.observation = observation
        self.calls = 0

    def process_frame(self, frame: object) -> PhoneObservation:
        self.calls += 1
        return self.observation


class NoFaceResult:
    face_landmarks = None
    facial_transformation_matrixes = None


def test_engine_initializes_independent_no_face_outputs() -> None:
    face = FakeFaceProvider(NoFaceResult())
    engine = DriverMonitoringEngine(
        face_provider=face,
        clock=lambda: 10.0,
    )

    output = engine.update("frame", 100)

    assert output.face_status is FaceFrameStatus.NO_FACE
    assert output.drowsiness.status is DrowsinessFrameStatus.NO_FACE
    assert output.drowsiness.perclos_percent == 0.0
    assert output.phone.status is PhoneFrameStatus.UNAVAILABLE
    assert face.calls == [("frame", 100)]


def test_engine_maps_face_provider_failure_to_unavailable() -> None:
    engine = DriverMonitoringEngine(
        face_provider=FakeFaceProvider(RuntimeError("provider failed")),
        phone_provider=FakePhoneProvider(
            PhoneObservation(PhoneFrameStatus.NOT_DETECTED)
        ),
        clock=lambda: 20.0,
    )

    output = engine.update("frame", 100)

    assert output.face_status is FaceFrameStatus.UNAVAILABLE
    assert output.drowsiness.status is DrowsinessFrameStatus.UNAVAILABLE
    assert output.phone.status is PhoneFrameStatus.NOT_DETECTED


def test_engine_collects_phone_detection_independently() -> None:
    detection = PhoneDetection(
        confidence=0.91,
        x1=0.1,
        y1=0.2,
        x2=0.4,
        y2=0.7,
    )
    phone = FakePhoneProvider(
        PhoneObservation(PhoneFrameStatus.DETECTED, (detection,))
    )
    engine = DriverMonitoringEngine(
        face_provider=FakeFaceProvider(NoFaceResult()),
        phone_provider=phone,
        clock=lambda: 30.0,
    )

    output = engine.update("frame", 100)

    assert output.phone.status is PhoneFrameStatus.DETECTED
    assert output.phone.detections == (detection,)
    assert phone.calls == 1


def test_engine_rejects_out_of_order_media_pipe_timestamp() -> None:
    engine = DriverMonitoringEngine(
        face_provider=FakeFaceProvider(NoFaceResult()),
        clock=lambda: 40.0,
    )

    engine.update("frame", 100)
    with pytest.raises(ValueError, match="strictly greater"):
        engine.update("frame", 100)


def test_engine_maps_phone_provider_failure_to_unavailable() -> None:
    class FailingPhoneProvider:
        def process_frame(self, frame: object) -> PhoneObservation:
            raise RuntimeError("phone provider failed")

    engine = DriverMonitoringEngine(
        face_provider=FakeFaceProvider(NoFaceResult()),
        phone_provider=FailingPhoneProvider(),
        clock=lambda: 50.0,
    )

    output = engine.update("frame", 100)

    assert output.phone.status is PhoneFrameStatus.UNAVAILABLE


def test_engine_uses_first_face_landmark_list_not_face_collection() -> None:
    landmarks = [
        SimpleNamespace(x=0.5, y=0.5, z=0.0)
        for _ in range(478)
    ]
    for index in (33, 133, 160, 158, 153, 144):
        landmarks[index].x = 0.5
        landmarks[index].y = 0.5
    for index in (362, 263, 385, 387, 373, 380):
        landmarks[index].x = 0.5
        landmarks[index].y = 0.5
    for index in range(468, 473):
        landmarks[index].x = 0.5
        landmarks[index].y = 0.5
    for index in range(473, 478):
        landmarks[index].x = 0.5
        landmarks[index].y = 0.5
    landmarks[33].x = 0.3
    landmarks[133].x = 0.7
    landmarks[362].x = 0.3
    landmarks[263].x = 0.7
    landmarks[385].y = 0.3
    landmarks[387].y = 0.7
    landmarks[373].y = 0.3
    landmarks[380].y = 0.7

    result = SimpleNamespace(
        face_landmarks=[landmarks],
        facial_transformation_matrixes=None,
    )
    calibrations = {
        "right_eye": EyeCalibration(
            eye="right_eye",
            neutral_horizontal=0.5,
            neutral_vertical=0.5,
            horizontal_min=0.3,
            horizontal_max=0.7,
            vertical_min=0.3,
            vertical_max=0.7,
            sample_count=100,
        ),
        "left_eye": EyeCalibration(
            eye="left_eye",
            neutral_horizontal=0.5,
            neutral_vertical=0.5,
            horizontal_min=0.3,
            horizontal_max=0.7,
            vertical_min=0.3,
            vertical_max=0.7,
            sample_count=100,
        ),
    }
    engine = DriverMonitoringEngine(
        face_provider=FakeFaceProvider(result),
        gaze_calibrations=calibrations,
        clock=lambda: 60.0,
    )

    output = engine.update("frame", 100)

    assert output.face_status is FaceFrameStatus.AVAILABLE
    assert output.drowsiness.status is not DrowsinessFrameStatus.UNAVAILABLE


def test_engine_reports_prolonged_closure_test_after_four_seconds() -> None:
    landmarks = [
        SimpleNamespace(x=0.5, y=0.5, z=0.0)
        for _ in range(478)
    ]
    landmarks[33].x = 0.0
    landmarks[133].x = 1.0
    landmarks[160].y = 0.49
    landmarks[144].y = 0.51
    landmarks[158].y = 0.49
    landmarks[153].y = 0.51
    landmarks[362].x = 0.0
    landmarks[263].x = 1.0
    landmarks[385].y = 0.49
    landmarks[380].y = 0.51
    landmarks[387].y = 0.49
    landmarks[373].y = 0.51

    drowsiness = DrowsinessConfig(
        perclos_window_seconds=60.0,
        closure_score_threshold=0.8,
        blink_exclusion_seconds=0.2,
        prolonged_closure_test_seconds=4.0,
        open_openness_baseline=0.3298,
        closed_openness_baseline=0.0736,
    )
    engine = DriverMonitoringEngine(
        drowsiness=drowsiness,
        clock=lambda: 100.0,
    )

    first = engine._process_drowsiness(
        FaceFrameStatus.AVAILABLE,
        landmarks,
        100,
    )
    second = engine._process_drowsiness(
        FaceFrameStatus.AVAILABLE,
        landmarks,
        4_100,
    )

    assert first.status is DrowsinessFrameStatus.CLOSED
    assert second.status is DrowsinessFrameStatus.PROLONGED_CLOSURE_TEST


def test_engine_closes_face_provider_when_phone_enter_fails() -> None:
    class ContextFaceProvider(FakeFaceProvider):
        def __init__(self) -> None:
            super().__init__(NoFaceResult())
            self.exited = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.exited = True

    class FailingPhoneContext:
        def __enter__(self):
            raise RuntimeError("phone initialization failed")

    face = ContextFaceProvider()
    engine = DriverMonitoringEngine(
        face_provider=face,
        phone_provider=FailingPhoneContext(),
    )

    with pytest.raises(RuntimeError, match="phone initialization"):
        with engine:
            pass

    assert face.exited
