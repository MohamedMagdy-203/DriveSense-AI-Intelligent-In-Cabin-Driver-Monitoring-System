"""Simple end-to-end webcam runtime for DriveSense integration monitoring."""

from __future__ import annotations

import platform
import argparse
import re
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from drivesense.engine import DriverMonitoringEngine
from drivesense.config import load_config
from drivesense.face.runtime import MediaPipeFaceProvider
from drivesense.phone.runtime import (
    AsyncYOLOPhoneProvider,
    YOLOPhoneProvider,
)
from drivesense.visual_distraction.gaze.calibration import EyeCalibration


WINDOW_NAME = "DriveSense End-to-End Runtime"
CALIBRATION_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "face_landmarker"
    / "gaze"
    / "calibration_results.md"
)
CALIBRATION_ROW = re.compile(
    r"\| (right_eye|left_eye) \| ([\d.]+) \| ([\d.]+) \| "
    r"\[([\d.]+), ([\d.]+)\] \| \[([\d.]+), ([\d.]+)\] \| (\d+) \|"
)


def open_camera(index: int) -> cv2.VideoCapture:
    camera = cv2.VideoCapture(index)
    if platform.system() == "Windows" and not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if camera.isOpened():
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera


def load_gaze_calibrations() -> dict[str, EyeCalibration]:
    if not CALIBRATION_PATH.is_file():
        return {}

    calibrations: dict[str, EyeCalibration] = {}
    for line in CALIBRATION_PATH.read_text(encoding="utf-8").splitlines():
        match = CALIBRATION_ROW.fullmatch(line)
        if match is None:
            continue
        eye, neutral_h, neutral_v, h_min, h_max, v_min, v_max, count = (
            match.groups()
        )
        calibrations[eye] = EyeCalibration(
            eye=eye,
            neutral_horizontal=float(neutral_h),
            neutral_vertical=float(neutral_v),
            horizontal_min=float(h_min),
            horizontal_max=float(h_max),
            vertical_min=float(v_min),
            vertical_max=float(v_max),
            sample_count=int(count),
        )
    return calibrations


def draw_status(
    frame,
    output,
    fps: float,
    frame_ms: float,
    rss_mb: float,
) -> None:
    cv2.rectangle(frame, (8, 8), (390, 210), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"FPS: {fps:.1f} | Frame: {frame_ms:.1f} ms",
        (16, 34),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"RAM: {rss_mb:.1f} MB",
        (16, 58),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Face: {output.face_status.value}",
        (16, 82),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0)
        if output.face_status.value == "AVAILABLE"
        else (0, 165, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Gaze: {output.gaze.gaze_status.value}",
        (16, 106),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Drowsiness: {output.drowsiness.status.value}",
        (16, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"PERCLOS: "
        f"{output.drowsiness.perclos_percent or 0.0:.1f}%"
        if output.drowsiness.perclos_percent is not None
        else "PERCLOS: UNAVAILABLE",
        (16, 154),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Distraction: {output.distraction.status.value}",
        (16, 178),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Phone: {output.phone.status.value}"
        f" / {output.phone.freshness.value}",
        (16, 202),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    height, width = frame.shape[:2]
    for detection in output.phone.detections:
        if output.phone.is_stale:
            continue
        x1 = int(detection.x1 * width)
        y1 = int(detection.y1 * height)
        x2 = int(detection.x2 * width)
        y2 = int(detection.y2 * height)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(
            frame,
            f"phone {detection.confidence:.2f}",
            (x1, max(y1 - 6, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the DriveSense end-to-end webcam integration monitor."
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Optional test duration in seconds. 0 runs until Q/Esc.",
    )
    parser.add_argument(
        "--phone-interval",
        type=float,
        default=0.5,
        help="Minimum seconds between asynchronous phone inference runs.",
    )
    parser.add_argument(
        "--record-output",
        type=Path,
        default=None,
        help="Optional MP4 or AVI path for a demonstration recording.",
    )
    args = parser.parse_args()
    if args.duration < 0:
        raise ValueError("--duration must be non-negative.")
    if args.phone_interval <= 0:
        raise ValueError("--phone-interval must be positive.")

    camera = open_camera(0)
    if not camera.isOpened():
        raise RuntimeError(
            "Could not open webcam 0. Check Windows camera permissions."
        )

    phone = AsyncYOLOPhoneProvider(
        YOLOPhoneProvider(),
        interval_seconds=args.phone_interval,
    )
    face = MediaPipeFaceProvider()
    app_config = load_config()
    engine = DriverMonitoringEngine(
        face_provider=face,
        phone_provider=phone,
        gaze_calibrations=load_gaze_calibrations(),
        drowsiness=app_config.drowsiness,
        temporal=app_config.temporal,
    )
    process = psutil.Process()
    process.cpu_percent(interval=None)
    frame_times = deque(maxlen=30)
    cpu_samples = deque(maxlen=300)
    initial_rss_mb = process.memory_info().rss / (1024 * 1024)
    peak_rss_mb = initial_rss_mb
    final_rss_mb = initial_rss_mb
    camera_read_failures = 0
    previous_timestamp_ms = int(time.perf_counter() * 1000)
    runtime_started = time.perf_counter()
    processed_frames = 0
    video_writer = None
    if args.record_output is not None:
        args.record_output.parent.mkdir(parents=True, exist_ok=True)
        video_writer = cv2.VideoWriter(
            str(args.record_output),
            cv2.VideoWriter_fourcc(*"mp4v"),
            30.0,
            (640, 480),
        )
        if not video_writer.isOpened():
            video_writer.release()
            video_writer = None
            raise RuntimeError(
                f"Could not open demo recording path: {args.record_output}"
            )
        print(f"Recording demo: {args.record_output}")
    print("Press Q or Esc to stop.")

    try:
        with engine:
            while True:
                if (
                    args.duration > 0
                    and time.perf_counter() - runtime_started
                    >= args.duration
                ):
                    break
                frame_started = time.perf_counter()
                success, frame = camera.read()
                if not success:
                    camera_read_failures += 1
                    if camera_read_failures >= 30:
                        raise RuntimeError(
                            "The webcam stopped returning frames."
                        )
                    continue

                camera_read_failures = 0
                timestamp_ms = max(
                    previous_timestamp_ms + 1,
                    int(time.perf_counter() * 1000),
                )
                previous_timestamp_ms = timestamp_ms
                output = engine.update(frame, timestamp_ms)
                processed_frames += 1
                frame_ms = (time.perf_counter() - frame_started) * 1000
                frame_times.append(frame_ms)
                fps = (
                    1000.0 / (sum(frame_times) / len(frame_times))
                    if frame_times
                    else 0.0
                )
                rss_mb = process.memory_info().rss / (1024 * 1024)
                final_rss_mb = rss_mb
                peak_rss_mb = max(peak_rss_mb, rss_mb)
                cpu_samples.append(process.cpu_percent(interval=None))
                draw_status(frame, output, fps, frame_ms, rss_mb)
                if video_writer is not None:
                    video_writer.write(frame)
                cv2.imshow(WINDOW_NAME, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
    finally:
        phone.close()
        camera.release()
        if video_writer is not None:
            video_writer.release()
        cv2.destroyAllWindows()
        elapsed = time.perf_counter() - runtime_started
        average_ms = (
            sum(frame_times) / len(frame_times)
            if frame_times
            else 0.0
        )
        print("\nRuntime smoke summary")
        print(f"Duration: {elapsed:.2f} s")
        print(f"Processed frames: {processed_frames}")
        print(f"Camera read failures: {camera_read_failures}")
        print(f"Average frame loop: {average_ms:.2f} ms")
        print(f"Initial RSS: {initial_rss_mb:.2f} MB")
        print(f"Final RSS: {final_rss_mb:.2f} MB")
        print(f"Peak RSS: {peak_rss_mb:.2f} MB")
        print(
            f"Average process CPU: "
            f"{sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0:.2f}%"
        )
        print(
            f"Average FPS: "
            f"{(1000.0 / average_ms if average_ms > 0 else 0.0):.2f}"
        )


if __name__ == "__main__":
    main()
