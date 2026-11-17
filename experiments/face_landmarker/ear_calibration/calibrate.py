"""Collect EAR calibration samples and write summary reports."""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from drivesense.face.runtime import (
    EAR_POINTS,
    WINDOW_NAME,
    create_landmarker,
    eye_aspect_ratio,
    face_image,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)

OUTPUT_DIR = Path(__file__).parent


def _collect(duration: int, every_frame: bool) -> list[float]:
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")
    samples: list[float] = []
    started = time.perf_counter()
    next_sample = started + 1
    timestamp_ms = int(started * 1000)
    try:
        with create_landmarker() as landmarker:
            while time.perf_counter() - started < duration:
                frame = read_gstreamer_frame(process.stdout)
                if frame is None:
                    raise RuntimeError("GStreamer stopped returning frames.")
                timestamp_ms += 1
                result = landmarker.detect_for_video(face_image(frame), timestamp_ms)
                if result.face_landmarks:
                    face = result.face_landmarks[0]
                    ear = (
                        eye_aspect_ratio(face, EAR_POINTS["right_eye"])
                        + eye_aspect_ratio(face, EAR_POINTS["left_eye"])
                    ) / 2
                    now = time.perf_counter()
                    if every_frame or now >= next_sample:
                        samples.append(ear)
                        next_sample += 1
                cv2.putText(frame, "Calibration | Q/Esc: exit", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    raise KeyboardInterrupt
    finally:
        stop_gstreamer(process)
        cv2.destroyAllWindows()
    return samples


def _write_minute_calibration(samples: list[float]) -> None:
    if not samples:
        raise RuntimeError("No EAR samples were collected.")
    report = f"""# EAR Calibration Results

Each condition was measured for 30 seconds using GStreamer and MediaPipe CPU.

| Status | Min EAR | Max EAR | Mean EAR |
|---|---:|---:|---:|
| Open Eyes | {min(samples):.3f} | {max(samples):.3f} | {statistics.fmean(samples):.3f} |
"""
    (OUTPUT_DIR / "results.md").write_text(report, encoding="utf-8")


def _write_frame_calibration(samples: list[float]) -> None:
    values = np.asarray(samples, dtype=np.float64)
    if len(values) < 2:
        raise RuntimeError("Fewer than two valid EAR frames were collected.")
    report = f"""# EAR Open-Eyes Frame Calibration Results

EAR was recorded for every detected-face frame during a 30-second test with
natural blinking. MediaPipe ran on CPU using GStreamer camera input.

- Valid EAR frames: `{len(values)}`
- Mean EAR: `{values.mean():.4f}`
- Standard deviation: `{values.std(ddof=1):.4f}`
- Minimum EAR: `{values.min():.4f}`
- Maximum EAR: `{values.max():.4f}`
- 5th percentile: `{np.percentile(values, 5):.4f}`
- 95th percentile: `{np.percentile(values, 95):.4f}`
"""
    (OUTPUT_DIR / "open_frame_results.md").write_text(report, encoding="utf-8")


def main() -> None:
    if "--open-frame" in __import__("sys").argv:
        samples = _collect(30, every_frame=True)
        _write_frame_calibration(samples)
    else:
        samples = _collect(30, every_frame=False)
        _write_minute_calibration(samples)


if __name__ == "__main__":
    main()
