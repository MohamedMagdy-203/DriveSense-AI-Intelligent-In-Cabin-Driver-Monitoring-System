"""Collect a short natural-gaze calibration session."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import cv2

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from drivesense.face.runtime import (
    WINDOW_NAME,
    create_landmarker,
    face_image,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)
from drivesense.visual_distraction.gaze.calibration import calibrate_gaze
from drivesense.visual_distraction.gaze.geometry import (
    NormalizedIrisPosition,
    normalized_iris_positions,
)

OUTPUT_PATH = Path(__file__).with_name("calibration_results.md")
COUNTDOWN_SECONDS = 3
CALIBRATION_SECONDS = 10


def main() -> None:
    print("Natural gaze calibration")
    print("Keep your head still and look naturally at the camera.")
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")

    samples: list[dict[str, NormalizedIrisPosition]] = []
    timestamp_ms = int(time.perf_counter() * 1000)
    try:
        with create_landmarker() as landmarker:
            countdown_started = time.perf_counter()
            while time.perf_counter() - countdown_started < COUNTDOWN_SECONDS:
                frame = read_gstreamer_frame(process.stdout)
                if frame is None:
                    raise RuntimeError("GStreamer stopped returning frames.")
                remaining = COUNTDOWN_SECONDS - (
                    time.perf_counter() - countdown_started
                )
                cv2.putText(
                    frame,
                    f"Natural gaze calibration starts in {max(1, int(remaining) + 1)}",
                    (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    return

            started = time.perf_counter()
            while time.perf_counter() - started < CALIBRATION_SECONDS:
                frame = read_gstreamer_frame(process.stdout)
                if frame is None:
                    raise RuntimeError("GStreamer stopped returning frames.")
                timestamp_ms = max(
                    timestamp_ms + 1,
                    int(time.perf_counter() * 1000),
                )
                result = landmarker.detect_for_video(
                    face_image(frame), timestamp_ms
                )
                if result.face_landmarks:
                    samples.append(
                        normalized_iris_positions(result.face_landmarks[0])
                    )
                cv2.putText(
                    frame,
                    f"Collecting natural gaze: "
                    f"{time.perf_counter() - started:.1f}/{CALIBRATION_SECONDS}s",
                    (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    return
    finally:
        stop_gstreamer(process)
        cv2.destroyAllWindows()

    calibration = calibrate_gaze(samples)
    lines = [
        "# Natural Gaze Calibration",
        "",
        "This calibration records natural gaze while looking at the camera. "
        "It defines person-specific neutral references and observed geometric "
        "ranges only; it does not define gaze classes or thresholds.",
        "",
        f"- Calibration duration: `{CALIBRATION_SECONDS} seconds`",
        f"- Valid gaze samples: `{len(samples)}`",
        "",
        "| Eye | Neutral horizontal | Neutral vertical | Horizontal range | Vertical range | Samples |",
        "|---|---:|---:|---|---|---:|",
    ]
    for eye in ("right_eye", "left_eye"):
        values = calibration[eye]
        lines.append(
            f"| {values.eye} | {values.neutral_horizontal:.4f} | "
            f"{values.neutral_vertical:.4f} | "
            f"[{values.horizontal_min:.4f}, {values.horizontal_max:.4f}] | "
            f"[{values.vertical_min:.4f}, {values.vertical_max:.4f}] | "
            f"{values.sample_count} |"
        )
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Calibration results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
