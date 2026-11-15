"""Display MediaPipe face landmarks from the webcam without recording."""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import mediapipe as mp


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "face_landmarker.task"
WINDOW_NAME = "MediaPipe Face Landmarker Preview"


def main() -> None:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH),
        delegate=mp.tasks.BaseOptions.Delegate.CPU,
    )
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam at index 0.")

    started = time.perf_counter()
    frame_number = 0

    try:
        with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
            while True:
                success, frame = camera.read()
                if not success:
                    raise RuntimeError("The webcam stopped returning frames.")

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = int((time.perf_counter() - started) * 1000)
                result = landmarker.detect_for_video(image, timestamp_ms)

                height, width = frame.shape[:2]
                for face in result.face_landmarks:
                    for landmark in face:
                        x = min(max(int(landmark.x * width), 0), width - 1)
                        y = min(max(int(landmark.y * height), 0), height - 1)
                        cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

                frame_number += 1
                elapsed = time.perf_counter() - started
                fps = frame_number / elapsed if elapsed else 0.0
                cv2.putText(
                    frame,
                    f"CPU | FPS: {fps:.1f} | Press Q or Esc to exit",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow(WINDOW_NAME, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
