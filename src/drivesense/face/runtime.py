"""Shared runtime helpers for CPU MediaPipe face-landmark experiments."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from drivesense.config import load_config
from drivesense.integration_contract import (
    FaceFrameStatus,
    FaceObservation,
)


CONFIG = load_config()
ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = CONFIG.mediapipe.model_path
WIDTH = CONFIG.camera.width
HEIGHT = CONFIG.camera.height
CAMERA_INDEX = CONFIG.camera.index
WINDOW_NAME = CONFIG.camera.window_name

RIGHT_EYE_INDICES = (
    33, 7, 163, 144, 145, 153, 154, 155,
    133, 173, 157, 158, 159, 160, 161, 246,
)
LEFT_EYE_INDICES = (
    362, 382, 381, 380, 374, 373, 390, 249,
    263, 466, 388, 387, 386, 385, 384, 398,
)
EYE_GROUPS = {"right_eye": RIGHT_EYE_INDICES, "left_eye": LEFT_EYE_INDICES}
EAR_POINTS = {
    "right_eye": (33, 160, 158, 133, 153, 144),
    "left_eye": (362, 385, 387, 263, 373, 380),
}


def create_landmarker():
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH),
            delegate=mp.tasks.BaseOptions.Delegate.CPU,
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=(
            CONFIG.mediapipe.min_face_detection_confidence
        ),
        min_face_presence_confidence=(
            CONFIG.mediapipe.min_face_presence_confidence
        ),
        min_tracking_confidence=CONFIG.mediapipe.min_tracking_confidence,
        output_facial_transformation_matrixes=True,
    )
    return mp.tasks.vision.FaceLandmarker.create_from_options(options)


def start_gstreamer() -> subprocess.Popen:
    gst_launch = shutil.which("gst-launch-1.0")
    if gst_launch is None:
        candidate = ROOT / ".venv" / "Scripts" / "gst-launch-1.0.exe"
        if candidate.is_file():
            gst_launch = str(candidate)
    if gst_launch is None:
        raise RuntimeError("Could not find gst-launch-1.0.")

    return subprocess.Popen(
        [
            gst_launch, "-q", "ksvideosrc", f"device-index={CAMERA_INDEX}",
            "!", "videoconvert", "!", "videoscale", "!",
            f"video/x-raw,format=BGR,width={WIDTH},height={HEIGHT}",
            "!", "fdsink", "fd=1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )


def read_gstreamer_frame(stream):
    frame_size = WIDTH * HEIGHT * 3
    data = bytearray()
    while len(data) < frame_size:
        chunk = stream.read(frame_size - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))


def stop_gstreamer(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def eye_aspect_ratio(face_landmarks: list[object], points: tuple[int, ...]) -> float:
    p1, p2, p3, p4, p5, p6 = (face_landmarks[index] for index in points)

    def distance(first: object, second: object) -> float:
        return float(((first.x - second.x) ** 2 + (first.y - second.y) ** 2) ** 0.5)

    horizontal = distance(p1, p4)
    if horizontal == 0:
        raise ValueError("Eye corner landmarks have zero distance.")
    return (distance(p2, p6) + distance(p3, p5)) / (2 * horizontal)


def eye_openness(face_landmarks: list[object], points: tuple[int, ...]) -> float:
    p1, p2, p3, p4, p5, p6 = (
        face_landmarks[index] for index in points
    )

    def distance(first: object, second: object) -> float:
        return float(((first.x - second.x) ** 2 + (first.y - second.y) ** 2) ** 0.5)

    width = distance(p1, p4)
    if width == 0:
        raise ValueError("Eye corner landmarks have zero distance.")
    vertical_opening = (distance(p2, p6) + distance(p3, p5)) / 2
    return vertical_opening / width


def face_image(frame):
    return mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
    )


def draw_landmark(frame, index: int, landmark: object, color: tuple[int, int, int]) -> None:
    height, width = frame.shape[:2]
    x = min(max(int(landmark.x * width), 0), width - 1)
    y = min(max(int(landmark.y * height), 0), height - 1)
    cv2.circle(frame, (x, y), 3, color, -1)
    cv2.putText(frame, str(index), (x + 3, y - 3),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)


def print_landmark_output(face_landmarks: list[object]) -> None:
    print(f"Number of landmarks: {len(face_landmarks)}")
    print("Landmark coordinates (normalized x, y, z):")
    for index, landmark in enumerate(face_landmarks):
        print(f"  {index:>3}: x={landmark.x:.6f}, "
              f"y={landmark.y:.6f}, z={landmark.z:.6f}")
    print("\nEye landmark indices:")
    for name, indices in EYE_GROUPS.items():
        print(f"  {name}: {list(indices)}")


class MediaPipeFaceProvider:
    """Synchronous Face Landmarker provider for the integration engine."""

    def __init__(self) -> None:
        self._landmarker = None

    def __enter__(self) -> "MediaPipeFaceProvider":
        self._landmarker = create_landmarker()
        self._landmarker.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._landmarker is not None:
            self._landmarker.__exit__(exc_type, exc_value, traceback)
            self._landmarker = None

    def process_frame(self, frame: object, timestamp_ms: int) -> object:
        if self._landmarker is None:
            raise RuntimeError("MediaPipeFaceProvider is not initialized.")
        result = self._landmarker.detect_for_video(
            face_image(frame),
            timestamp_ms,
        )
        return face_observation_from_result(result, timestamp_ms)


def face_observation_from_result(
    result: object,
    timestamp_ms: int,
) -> FaceObservation:
    """Convert a MediaPipe result into the engine-facing face contract."""
    face_sets = getattr(result, "face_landmarks", None)
    if not face_sets:
        return FaceObservation(
            FaceFrameStatus.NO_FACE,
            timestamp_ms=timestamp_ms,
        )
    landmarks = tuple(face_sets[0])
    if len(landmarks) < 478:
        raise ValueError(
            "The first face has fewer than 478 MediaPipe landmarks."
        )
    matrices = getattr(result, "facial_transformation_matrixes", None)
    facial_matrix = None
    if matrices:
        try:
            facial_matrix = matrices[0]
        except (IndexError, TypeError):
            facial_matrix = None
    return FaceObservation(
        FaceFrameStatus.AVAILABLE,
        landmarks=landmarks,
        facial_matrix=facial_matrix,
        timestamp_ms=timestamp_ms,
    )
