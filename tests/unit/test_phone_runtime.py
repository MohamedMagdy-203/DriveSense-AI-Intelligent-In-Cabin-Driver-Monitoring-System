from types import SimpleNamespace

import pytest

from drivesense.integration_contract import (
    PhoneFrameStatus,
    PhoneResultFreshness,
)
from drivesense.phone.runtime import (
    AsyncYOLOPhoneProvider,
    YOLOPhoneProvider,
)


class FakeFrame:
    shape = (480, 640, 3)


class FakeModel:
    def __init__(self, prediction: object) -> None:
        self.prediction = prediction

    def predict(self, **kwargs):
        return [self.prediction]


class FakeBoxes:
    def __init__(self) -> None:
        self.xyxy = [[64.0, 48.0, 320.0, 384.0]]
        self.conf = [0.91]
        self.cls = [0.0]

    def __len__(self) -> int:
        return 1


def test_phone_provider_converts_detection(tmp_path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")
    provider = YOLOPhoneProvider(
        checkpoint,
        model=FakeModel(SimpleNamespace(boxes=FakeBoxes())),
    )

    observation = provider.process_frame(FakeFrame())

    assert observation.status is PhoneFrameStatus.DETECTED
    assert len(observation.detections) == 1
    detection = observation.detections[0]
    assert detection.confidence == pytest.approx(0.91)
    assert detection.x1 == pytest.approx(0.1)
    assert detection.y1 == pytest.approx(0.1)
    assert detection.x2 == pytest.approx(0.5)
    assert detection.y2 == pytest.approx(0.8)


def test_phone_provider_maps_empty_boxes_to_not_detected(tmp_path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")

    class EmptyBoxes:
        xyxy = []
        conf = []
        cls = []

        def __len__(self) -> int:
            return 0

    boxes = EmptyBoxes()
    provider = YOLOPhoneProvider(
        checkpoint,
        model=FakeModel(SimpleNamespace(boxes=boxes)),
    )

    observation = provider.process_frame(FakeFrame())

    assert observation.status is PhoneFrameStatus.NOT_DETECTED


def test_phone_provider_maps_prediction_failure_to_unavailable(tmp_path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")

    class FailingModel:
        def predict(self, **kwargs):
            raise RuntimeError("CUDA inference failed")

    provider = YOLOPhoneProvider(
        checkpoint,
        model=FailingModel(),
    )

    observation = provider.process_frame(FakeFrame())

    assert observation.status is PhoneFrameStatus.UNAVAILABLE
    assert isinstance(provider.last_error, RuntimeError)


def test_phone_provider_rejects_missing_checkpoint(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="checkpoint"):
        YOLOPhoneProvider(
            tmp_path / "missing.pt",
            model=object(),
        )


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_phone_provider_rejects_invalid_confidence(
    tmp_path,
    confidence: float,
) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")

    with pytest.raises(ValueError, match="confidence_threshold"):
        YOLOPhoneProvider(checkpoint, confidence_threshold=confidence)


def test_async_phone_provider_returns_cache_without_blocking(tmp_path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")

    class AsyncModel:
        def predict(self, **kwargs):
            raise RuntimeError("inference not available")

    provider = YOLOPhoneProvider(checkpoint, model=AsyncModel())
    async_provider = AsyncYOLOPhoneProvider(
        provider,
        interval_seconds=60,
    )
    try:
        observation = async_provider.process_frame(FakeFrame())
        assert observation.status is PhoneFrameStatus.UNAVAILABLE
    finally:
        async_provider.close()


def test_sync_phone_provider_marks_completed_result_fresh(tmp_path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")
    provider = YOLOPhoneProvider(
        checkpoint,
        model=FakeModel(SimpleNamespace(boxes=FakeBoxes())),
    )

    observation = provider.process_frame(FakeFrame())

    assert observation.freshness is PhoneResultFreshness.FRESH
    assert observation.timestamp_monotonic is not None


def test_async_phone_provider_marks_cached_and_stale_results(tmp_path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")
    provider = YOLOPhoneProvider(
        checkpoint,
        model=FakeModel(SimpleNamespace(boxes=FakeBoxes())),
    )
    clock = [100.0]
    async_provider = AsyncYOLOPhoneProvider(
        provider,
        interval_seconds=1.0,
        stale_threshold_seconds=2.0,
        clock=lambda: clock[0],
    )
    try:
        initial = async_provider.process_frame(FakeFrame())
        assert initial.status in (
            PhoneFrameStatus.UNAVAILABLE,
            PhoneFrameStatus.DETECTED,
        )

        import time
        deadline = time.monotonic() + 2
        while async_provider._inference_running:
            if time.monotonic() >= deadline:
                break
            time.sleep(0.01)

        cached = async_provider.process_frame(FakeFrame())
        assert cached.freshness in (
            PhoneResultFreshness.FRESH,
            PhoneResultFreshness.CACHED,
            PhoneResultFreshness.UNAVAILABLE,
        )

        clock[0] = 103.0
        stale = async_provider.process_frame(FakeFrame())
        if stale.status is PhoneFrameStatus.DETECTED:
            assert stale.freshness is PhoneResultFreshness.STALE
    finally:
        async_provider.close()


def test_async_phone_provider_close_is_idempotent(tmp_path) -> None:
    checkpoint = tmp_path / "best.pt"
    checkpoint.write_bytes(b"fake")
    provider = YOLOPhoneProvider(
        checkpoint,
        model=FakeModel(SimpleNamespace(boxes=FakeBoxes())),
    )
    async_provider = AsyncYOLOPhoneProvider(provider)

    async_provider.close()
    async_provider.close()

    observation = async_provider.process_frame(FakeFrame())
    assert observation.status is PhoneFrameStatus.UNAVAILABLE
    assert observation.freshness is PhoneResultFreshness.UNAVAILABLE
