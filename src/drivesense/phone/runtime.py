"""YOLO runtime adapter for phone detection."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
import threading
import time

from drivesense.integration_contract import (
    PhoneDetection,
    PhoneFrameStatus,
    PhoneObservation,
    PhoneResultFreshness,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CHECKPOINT = (
    PROJECT_ROOT
    / "artifacts"
    / "phone_detection"
    / "weights"
    / "best.pt"
)


class YOLOPhoneProvider:
    """Adapt Ultralytics YOLO phone predictions to the engine contract."""

    def __init__(
        self,
        checkpoint: str | Path = DEFAULT_CHECKPOINT,
        *,
        image_size: int = 640,
        confidence_threshold: float = 0.25,
        device: str | int = 0,
        require_cuda: bool = True,
        model: object | None = None,
    ) -> None:
        if image_size <= 0:
            raise ValueError("image_size must be positive.")
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1.")

        self.checkpoint = Path(checkpoint)
        self.image_size = image_size
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.require_cuda = require_cuda
        self._model = model
        self._torch = None
        self.last_error: Exception | None = None

        if not self.checkpoint.is_file():
            raise FileNotFoundError(
                f"Trained phone checkpoint not found: {self.checkpoint}"
            )

        if self._model is None:
            self._load_model()

    def _load_model(self) -> None:
        try:
            import torch
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Phone detection requires torch and ultralytics."
            ) from exc

        if self.require_cuda and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is not available. Install/use CUDA-enabled PyTorch "
                "before initializing the YOLO phone provider."
            )
        if self.require_cuda:
            torch.cuda.set_device(int(self.device))

        self._torch = torch
        self._model = YOLO(str(self.checkpoint))

    def process_frame(self, frame: object) -> PhoneObservation:
        """Run inference and return only contract-level phone observations."""
        if self._model is None:
            return PhoneObservation(PhoneFrameStatus.UNAVAILABLE)

        try:
            predictions = self._model.predict(
                source=frame,
                imgsz=self.image_size,
                conf=self.confidence_threshold,
                device=self.device,
                verbose=False,
            )
            if not predictions:
                observation = PhoneObservation(
                    PhoneFrameStatus.UNAVAILABLE,
                    freshness=PhoneResultFreshness.UNAVAILABLE,
                )
            else:
                observation = self._convert_result(predictions[0], frame)
        except (RuntimeError, ValueError, TypeError, AttributeError) as exc:
            self.last_error = exc
            observation = PhoneObservation(
                PhoneFrameStatus.UNAVAILABLE,
                freshness=PhoneResultFreshness.UNAVAILABLE,
            )
        if observation.status is PhoneFrameStatus.UNAVAILABLE:
            return observation
        return replace(
            observation,
            timestamp_monotonic=time.monotonic(),
            freshness=PhoneResultFreshness.FRESH,
        )

    def close(self) -> None:
        """Release provider-owned resources if a backend provides close()."""
        close = getattr(self._model, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> "YOLOPhoneProvider":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _convert_result(
        self,
        result: object,
        frame: object,
    ) -> PhoneObservation:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return PhoneObservation(PhoneFrameStatus.NOT_DETECTED)

        try:
            count = int(len(boxes))
        except (TypeError, ValueError):
            return PhoneObservation(PhoneFrameStatus.UNAVAILABLE)
        if count == 0:
            return PhoneObservation(PhoneFrameStatus.NOT_DETECTED)

        frame_width, frame_height = _frame_dimensions(frame)
        if frame_width is None or frame_height is None:
            orig_shape = getattr(result, "orig_shape", None)
            if orig_shape:
                frame_height = int(orig_shape[0])
                frame_width = int(orig_shape[1])
        if not frame_width or not frame_height:
            return PhoneObservation(PhoneFrameStatus.UNAVAILABLE)

        xyxy = getattr(boxes, "xyxy", None)
        confidences = getattr(boxes, "conf", None)
        classes = getattr(boxes, "cls", None)
        if xyxy is None or confidences is None:
            return PhoneObservation(PhoneFrameStatus.UNAVAILABLE)

        coordinates = _to_rows(xyxy)
        confidence_rows = _to_rows(confidences)
        class_rows = _to_rows(classes) if classes is not None else []
        if len(coordinates) != len(confidence_rows):
            return PhoneObservation(PhoneFrameStatus.UNAVAILABLE)

        detections: list[PhoneDetection] = []
        for index, coordinate in enumerate(coordinates):
            if len(coordinate) < 4:
                continue
            if class_rows and len(class_rows[index]) > 0:
                class_id = float(class_rows[index][0])
                if class_id != 0:
                    continue

            confidence = float(confidence_rows[index][0])
            x1 = _clamp(coordinate[0] / frame_width)
            y1 = _clamp(coordinate[1] / frame_height)
            x2 = _clamp(coordinate[2] / frame_width)
            y2 = _clamp(coordinate[3] / frame_height)
            try:
                detections.append(
                    PhoneDetection(
                        confidence=_clamp(confidence),
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                    )
                )
            except ValueError:
                continue

        if detections:
            return PhoneObservation(
                PhoneFrameStatus.DETECTED,
                tuple(detections),
            )
        return PhoneObservation(PhoneFrameStatus.NOT_DETECTED)


def _frame_dimensions(frame: object) -> tuple[int | None, int | None]:
    shape = getattr(frame, "shape", None)
    if shape is not None and len(shape) >= 2:
        return int(shape[1]), int(shape[0])
    return None, None


def _to_rows(value: object) -> list[list[float]]:
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()

    if isinstance(value, (int, float)):
        return [[float(value)]]
    if not isinstance(value, (list, tuple)):
        return []

    rows: list[list[float]] = []
    for item in value:
        if isinstance(item, (list, tuple)):
            rows.append([float(part) for part in item])
        else:
            rows.append([float(item)])
    return rows


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


class AsyncYOLOPhoneProvider:
    """Throttle YOLO inference while preserving a non-blocking provider API."""

    def __init__(
        self,
        provider: YOLOPhoneProvider,
        *,
        interval_seconds: float = 0.5,
        stale_threshold_seconds: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive.")
        if stale_threshold_seconds is not None and stale_threshold_seconds <= 0:
            raise ValueError("stale_threshold_seconds must be positive.")
        self.provider = provider
        self.interval_seconds = interval_seconds
        self._clock = clock or time.monotonic
        self.stale_threshold_seconds = (
            stale_threshold_seconds
            if stale_threshold_seconds is not None
            else max(interval_seconds * 2.0, 1.0)
        )
        self._last_submission_monotonic = -interval_seconds
        self._inference_running = False
        self._closed = False
        self._lock = threading.Lock()
        self._observation = PhoneObservation(
            PhoneFrameStatus.UNAVAILABLE,
            freshness=PhoneResultFreshness.UNAVAILABLE,
        )
        self.last_error: Exception | None = None
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="drivesense-phone",
        )

    def process_frame(self, frame: object) -> PhoneObservation:
        now = self._clock()
        should_submit = False
        with self._lock:
            if self._closed:
                return PhoneObservation(
                    PhoneFrameStatus.UNAVAILABLE,
                    freshness=PhoneResultFreshness.UNAVAILABLE,
                )
            should_submit = (
                not self._inference_running
                and now - self._last_submission_monotonic
                >= self.interval_seconds
            )
            if should_submit:
                self._inference_running = True
                self._last_submission_monotonic = now

        if should_submit:
            inference_frame = _copy_frame(frame)
            self._executor.submit(
                self._run_inference,
                inference_frame,
            )
        with self._lock:
            observation = self._observation
            if observation.status is PhoneFrameStatus.UNAVAILABLE:
                return observation
            timestamp = observation.timestamp_monotonic
            if timestamp is None:
                return replace(
                    observation,
                    freshness=PhoneResultFreshness.UNKNOWN,
                )
            age = max(0.0, now - timestamp)
            if age >= self.stale_threshold_seconds:
                freshness = PhoneResultFreshness.STALE
            elif age > 0.0:
                freshness = PhoneResultFreshness.CACHED
            else:
                freshness = PhoneResultFreshness.FRESH
            return replace(observation, freshness=freshness)

    def _run_inference(self, frame: object) -> None:
        try:
            observation = self.provider.process_frame(frame)
        except (RuntimeError, ValueError, TypeError) as exc:
            self.provider.last_error = exc
            self.last_error = exc
            observation = PhoneObservation(
                PhoneFrameStatus.UNAVAILABLE,
                freshness=PhoneResultFreshness.UNAVAILABLE,
            )
        with self._lock:
            if self._closed:
                return
            if observation.status is not PhoneFrameStatus.UNAVAILABLE:
                observation = replace(
                    observation,
                    timestamp_monotonic=self._clock(),
                    freshness=PhoneResultFreshness.FRESH,
                )
            self._inference_running = False
            self._observation = observation

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._executor.shutdown(wait=True, cancel_futures=True)
        self.provider.close()

    def __enter__(self) -> "AsyncYOLOPhoneProvider":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _copy_frame(frame: object) -> object:
    copy_method = getattr(frame, "copy", None)
    if callable(copy_method):
        return copy_method()
    return frame
