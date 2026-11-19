"""Run the trained phone detector on a live webcam feed."""

from __future__ import annotations

import platform
import time
from collections import deque
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = PROJECT_ROOT / "artifacts" / "phone_detection" / "weights" / "best.pt"
CAMERA_INDEX = 0
IMAGE_SIZE = 640
CONFIDENCE_THRESHOLD = 0.25
WINDOW_NAME = "DriveSense Phone Detection"
FPS_HISTORY_SIZE = 30


def _open_camera(camera_index: int) -> cv2.VideoCapture:
    if platform.system() == "Windows":
        camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if camera.isOpened():
            return camera
        camera.release()

    return cv2.VideoCapture(camera_index)


def main() -> None:
    if not CHECKPOINT.is_file():
        raise FileNotFoundError(f"Trained checkpoint not found: {CHECKPOINT}")
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available in this Python environment. "
            "Install/use CUDA-enabled PyTorch before running live detection."
        )

    torch.cuda.set_device(0)
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Checkpoint: {CHECKPOINT}")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD:.2f}")
    print("Press Q or Esc to stop.")

    model = YOLO(str(CHECKPOINT))
    camera = _open_camera(CAMERA_INDEX)
    if not camera.isOpened():
        raise RuntimeError(
            f"Could not open camera index {CAMERA_INDEX}. "
            "Check Windows camera permissions and close apps that may be using it."
        )

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    frame_times: deque[float] = deque(maxlen=FPS_HISTORY_SIZE)

    try:
        while True:
            success, frame = camera.read()
            if not success:
                raise RuntimeError("The camera stopped returning frames.")

            started = time.perf_counter()
            result = model.predict(
                source=frame,
                imgsz=IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                device=0,
                verbose=False,
            )[0]
            annotated = result.plot()

            frame_times.append(time.perf_counter() - started)
            average_duration = sum(frame_times) / len(frame_times)
            fps = 1.0 / average_duration if average_duration > 0 else 0.0
            detection_count = len(result.boxes)

            cv2.putText(
                annotated,
                f"GPU: {torch.cuda.get_device_name(0)} | FPS: {fps:.1f}",
                (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                annotated,
                f"Phones detected: {detection_count}",
                (10, 56),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(WINDOW_NAME, annotated)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
