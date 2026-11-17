"""Live geometric gaze-classification demo using saved calibration."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import cv2

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from experiments.face_landmarker.common.runtime import (
    WINDOW_NAME,
    create_landmarker,
    face_image,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)
from experiments.face_landmarker.gaze.calibration import EyeCalibration
from experiments.face_landmarker.gaze.classification import classify_gaze
from experiments.face_landmarker.gaze.gaze import normalized_iris_positions

CALIBRATION_PATH = Path(__file__).with_name("calibration_results.md")
CALIBRATION_ROW = re.compile(
    r"\| (right_eye|left_eye) \| ([\d.]+) \| ([\d.]+) \| "
    r"\[([\d.]+), ([\d.]+)\] \| \[([\d.]+), ([\d.]+)\] \| (\d+) \|"
)


def _load_calibration() -> dict[str, EyeCalibration]:
    if not CALIBRATION_PATH.is_file():
        raise FileNotFoundError(f"Missing calibration file: {CALIBRATION_PATH}")
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
    if set(calibrations) != {"right_eye", "left_eye"}:
        raise ValueError(
            "Calibration must contain both right_eye and left_eye rows."
        )
    return calibrations


def main() -> None:
    calibrations = _load_calibration()
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")

    timestamp_ms = int(time.perf_counter() * 1000)
    try:
        with create_landmarker() as landmarker:
            while True:
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
                    positions = normalized_iris_positions(result.face_landmarks[0])
                    classification = classify_gaze(positions, calibrations)
                    cv2.putText(
                        frame,
                        f"Gaze: {classification.direction.value}",
                        (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )
                    for line, eye_result in enumerate(classification.eyes, 1):
                        cv2.putText(
                            frame,
                            f"{eye_result.eye}: "
                            f"H={eye_result.horizontal.value} "
                            f"V={eye_result.vertical.value}",
                            (10, 35 + line * 35),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            2,
                        )
                else:
                    cv2.putText(
                        frame,
                        "Gaze: NO_FACE",
                        (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2,
                    )
                cv2.putText(
                    frame,
                    "Q/Esc: exit | calibration: natural gaze",
                    (10, 145),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2,
                )
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        stop_gstreamer(process)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
