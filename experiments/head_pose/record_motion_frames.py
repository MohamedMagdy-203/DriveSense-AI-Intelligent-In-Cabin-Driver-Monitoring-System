"""Record facial transformation matrices for controlled head movements."""

from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.face_landmarker.common.runtime import (
    WINDOW_NAME,
    create_landmarker,
    face_image,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)
CSV_PATH = Path(__file__).with_name("motion_frames.csv")
REPORT_PATH = Path(__file__).with_name("motion_results.md")
POSE_DURATION_SECONDS = 3
COUNTDOWN_SECONDS = 8
POSES = (
    ("Neutral", "Keep your head straight."),
    ("Turn Left", "Turn left without looking up or down."),
    ("Turn Right", "Turn right without looking up or down."),
    ("Look Up", "Look up without turning left or right."),
    ("Look Down", "Look down without turning left or right."),
)
MATRIX_FIELDS = [
    f"m{row}{column}" for row in range(4) for column in range(4)
]
CSV_FIELDS = ["timestamp_ms", "pose", "frame_index", *MATRIX_FIELDS]


def _display_axes(matrix: np.ndarray) -> tuple[tuple[float, float, float], np.ndarray]:
    rotation = matrix[:3, :3]
    pitch = math.degrees(math.asin(float(np.clip(-rotation[2, 0], -1.0, 1.0))))
    yaw = math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))
    roll = math.degrees(math.atan2(rotation[2, 1], rotation[2, 2]))
    return (yaw, pitch, roll), rotation


def _show_frame(
    frame: np.ndarray,
    pose_name: str,
    instruction: str,
    elapsed: float,
    matrix: np.ndarray | None,
) -> None:
    lines = [
        f"{pose_name}: {instruction}",
        f"Recording: {elapsed:.1f}/{POSE_DURATION_SECONDS}s | Q/Esc: exit",
    ]
    if matrix is not None:
        (yaw, pitch, roll), axes = _display_axes(matrix)
        lines.extend(
            [
                f"Yaw {yaw:+.1f}  Pitch {pitch:+.1f}  Roll {roll:+.1f}",
                f"X [{axes[0, 0]:+.2f}, {axes[1, 0]:+.2f}, {axes[2, 0]:+.2f}]",
                f"Y [{axes[0, 1]:+.2f}, {axes[1, 1]:+.2f}, {axes[2, 1]:+.2f}]",
                f"Z [{axes[0, 2]:+.2f}, {axes[1, 2]:+.2f}, {axes[2, 2]:+.2f}]",
            ]
        )
    for line_number, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (10, 30 + line_number * 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2,
        )


def _countdown(process, pose_name: str, instruction: str) -> None:
    started = time.perf_counter()
    while time.perf_counter() - started < COUNTDOWN_SECONDS:
        frame = read_gstreamer_frame(process.stdout)
        if frame is None:
            raise RuntimeError("GStreamer stopped returning frames.")
        remaining = COUNTDOWN_SECONDS - (time.perf_counter() - started)
        cv2.putText(
            frame,
            f"{pose_name}: prepare ({max(1, math.ceil(remaining))})",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            instruction,
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            raise KeyboardInterrupt


def main() -> None:
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")

    rows: list[dict[str, object]] = []
    timestamp_ms = int(time.perf_counter() * 1000)
    try:
        with create_landmarker() as landmarker:
            for pose_name, instruction in POSES:
                print(f"{pose_name}: {instruction}")
                _countdown(process, pose_name, instruction)
                started = time.perf_counter()
                frame_index = 0
                while time.perf_counter() - started < POSE_DURATION_SECONDS:
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
                    latest_matrix = None
                    if result.facial_transformation_matrixes:
                        latest_matrix = np.asarray(
                            result.facial_transformation_matrixes[0]
                        )
                        if latest_matrix.shape != (4, 4):
                            raise ValueError(
                                "Expected a 4x4 facial transformation matrix, "
                                f"got {latest_matrix.shape}."
                            )
                        rows.append(
                            {
                                "timestamp_ms": timestamp_ms,
                                "pose": pose_name,
                                "frame_index": frame_index,
                                **{
                                    field: float(latest_matrix[row, column])
                                    for field, (row, column) in zip(
                                        MATRIX_FIELDS,
                                        (
                                            (row, column)
                                            for row in range(4)
                                            for column in range(4)
                                        ),
                                    )
                                },
                            }
                        )
                        frame_index += 1
                    _show_frame(
                        frame,
                        pose_name,
                        instruction,
                        time.perf_counter() - started,
                        latest_matrix,
                    )
                    cv2.imshow(WINDOW_NAME, frame)
                    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                        raise KeyboardInterrupt
    finally:
        stop_gstreamer(process)
        cv2.destroyAllWindows()

    with CSV_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    report_lines = [
        "# Head Pose Per-Frame Matrix Recording",
        "",
        "Each CSV row contains one `4x4` facial transformation matrix for the "
        "first detected face in one captured frame.",
        "",
        f"- Duration per pose: `{POSE_DURATION_SECONDS} seconds`",
        f"- Total recorded matrices: `{len(rows)}`",
        f"- CSV output: `{CSV_PATH.name}`",
        "",
        "| Pose | Recorded matrices |",
        "|---|---:|",
    ]
    for pose_name, _ in POSES:
        count = sum(row["pose"] == pose_name for row in rows)
        report_lines.append(f"| {pose_name} | {count} |")
    report_lines.extend(
        [
            "",
            "The provisional angle labels and axis vectors shown during capture "
            "are diagnostic only. Axis order and signs require comparison of "
            "these per-frame recordings.",
        ]
    )
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Recorded {len(rows)} matrices.")
    print(f"Frames written to {CSV_PATH}")
    print(f"Summary written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
