"""Calibrate landmark-based eye openness without an additional model."""

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
    eye_openness,
    face_image,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)

OUTPUT_PATH = Path(__file__).with_name("results.md")
DURATION_SECONDS = 30


def _openness(face: list[object], points: tuple[int, ...]) -> float:
    return eye_openness(face, points)


def _collect(label: str) -> list[float]:
    print(f"{label}: starting in 5 seconds; hold this position.")
    time.sleep(5)
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")

    values: list[float] = []
    started = time.perf_counter()
    next_progress = started + 1
    timestamp_ms = int(started * 1000)
    try:
        with create_landmarker() as landmarker:
            while time.perf_counter() - started < DURATION_SECONDS:
                frame = read_gstreamer_frame(process.stdout)
                if frame is None:
                    raise RuntimeError("GStreamer stopped returning frames.")
                timestamp_ms += 1
                result = landmarker.detect_for_video(face_image(frame), timestamp_ms)
                if result.face_landmarks:
                    face = result.face_landmarks[0]
                    right = _openness(face, EAR_POINTS["right_eye"])
                    left = _openness(face, EAR_POINTS["left_eye"])
                    values.append((right + left) / 2)

                now = time.perf_counter()
                if now >= next_progress:
                    print(f"{label}: {min(int(now - started), DURATION_SECONDS)}/"
                          f"{DURATION_SECONDS}s, valid frames={len(values)}")
                    next_progress += 1
                cv2.putText(frame, f"{label} | Q/Esc: exit", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    raise KeyboardInterrupt
    finally:
        stop_gstreamer(process)
        cv2.destroyAllWindows()
    if len(values) < 2:
        raise RuntimeError(f"Not enough valid frames collected for {label}.")
    return values


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "std": statistics.stdev(values),
        "p05": float(np.percentile(values, 5)),
        "p95": float(np.percentile(values, 95)),
    }


def main() -> None:
    print("Landmark-based Eye Openness calibration")
    print("First phase: keep eyes naturally open and blink normally.")
    open_values = _collect("Open Eyes")
    print("Second phase: half-close both eyes and hold a relaxed partial closure.")
    partial_values = _collect("Partial Closure")
    print("Third phase: close both eyes comfortably.")
    closed_values = _collect("Closed Eyes")
    open_stats = _summary(open_values)
    partial_stats = _summary(partial_values)
    closed_stats = _summary(closed_values)
    open_baseline = open_stats["mean"]
    closed_baseline = closed_stats["mean"]
    baseline_range = open_baseline - closed_baseline
    partial_closure = (
        (open_baseline - partial_stats["mean"]) / baseline_range
        if baseline_range > 0 else float("nan")
    )
    report = f"""# Landmark-Based Eye Openness Calibration

This experiment uses the existing MediaPipe Face Landmarker only. Eye openness
is the average eyelid aperture divided by eye-corner width for both eyes. This
is a geometric openness proxy, not direct pupil-occlusion segmentation.

- Duration per state: `{DURATION_SECONDS} seconds`
- Valid open-eye frames: `{len(open_values)}`
- Valid partial-closure frames: `{len(partial_values)}`
- Valid closed-eye frames: `{len(closed_values)}`

| State | Min | Max | Mean | Std Dev | 5th percentile | 95th percentile |
|---|---:|---:|---:|---:|---:|---:|
| Open Eyes | {open_stats["min"]:.4f} | {open_stats["max"]:.4f} | {open_stats["mean"]:.4f} | {open_stats["std"]:.4f} | {open_stats["p05"]:.4f} | {open_stats["p95"]:.4f} |
| Partial Closure | {partial_stats["min"]:.4f} | {partial_stats["max"]:.4f} | {partial_stats["mean"]:.4f} | {partial_stats["std"]:.4f} | {partial_stats["p05"]:.4f} | {partial_stats["p95"]:.4f} |
| Closed Eyes | {closed_stats["min"]:.4f} | {closed_stats["max"]:.4f} | {closed_stats["mean"]:.4f} | {closed_stats["std"]:.4f} | {closed_stats["p05"]:.4f} | {closed_stats["p95"]:.4f} |

## Provisional calibrated mapping

For a future closure estimate, use the open and closed baselines rather than a
fixed EAR threshold:

```text
closure = clamp((open_baseline - current_openness)
                / (open_baseline - closed_baseline), 0, 1)
```

Using the collected means, the partial-closure estimate is
`{partial_closure:.1%}` of the open-to-closed range. This is only a calibration
check; it is not direct measurement of 80% eyelid or pupil coverage.
"""
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
