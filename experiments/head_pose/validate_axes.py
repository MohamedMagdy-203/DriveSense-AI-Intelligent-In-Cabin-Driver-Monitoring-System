"""Validate head-pose rotation axes using the recorded per-frame matrices."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

MOTION_PATH = Path(__file__).with_name("motion_frames.csv")
OUTPUT_PATH = Path(__file__).with_name("axis_validation_results.md")
VECTORS_PATH = Path(__file__).with_name("motion_rotation_vectors.csv")
MATRIX_FIELDS = [
    f"m{row}{column}" for row in range(4) for column in range(4)
]
VECTOR_FIELDS = [
    "timestamp_ms",
    "pose",
    "frame_index",
    "rotation_x_deg",
    "rotation_y_deg",
    "rotation_z_deg",
    "rotation_magnitude_deg",
]
EXPECTED_SIGN = {
    "Turn Left": (2, -1),
    "Turn Right": (2, 1),
    "Look Up": (0, -1),
    "Look Down": (0, 1),
}


def _normalized_rotation(matrix: np.ndarray) -> np.ndarray:
    rotation = matrix[:3, :3].astype(float)
    scale = float(np.mean(np.linalg.norm(rotation, axis=0)))
    if scale <= 0:
        raise ValueError("Facial transformation matrix has zero rotation scale.")
    return rotation / scale


def _rotation_vector(rotation: np.ndarray) -> np.ndarray:
    cosine = float(np.clip((np.trace(rotation) - 1) / 2, -1.0, 1.0))
    angle = math.acos(cosine)
    skew = np.array(
        [
            rotation[2, 1] - rotation[1, 2],
            rotation[0, 2] - rotation[2, 0],
            rotation[1, 0] - rotation[0, 1],
        ]
    )
    if angle < 1e-8:
        return skew / 2
    sine = math.sin(angle)
    if abs(sine) > 1e-8:
        return skew * (angle / (2 * sine))

    diagonal = np.diag(rotation)
    axis = np.sqrt(np.maximum((diagonal + 1) / 2, 0))
    largest = int(np.argmax(axis))
    if axis[largest] < 1e-8:
        raise ValueError("Could not extract a rotation axis.")
    for index in range(3):
        if index != largest:
            axis[index] = (
                rotation[largest, index] + rotation[index, largest]
            ) / (4 * axis[largest])
    return axis * angle


def _relative_rotation_vector(
    matrix: np.ndarray,
    neutral_matrix: np.ndarray,
) -> np.ndarray:
    rotation = _normalized_rotation(matrix)
    neutral_rotation = _normalized_rotation(neutral_matrix)
    return _rotation_vector(neutral_rotation.T @ rotation)


def _load_matrices() -> dict[str, list[dict[str, object]]]:
    if not MOTION_PATH.is_file():
        raise FileNotFoundError(f"Missing recorded matrix file: {MOTION_PATH}")
    poses: dict[str, list[dict[str, object]]] = {}
    with MOTION_PATH.open(newline="", encoding="utf-8") as input_file:
        for row in csv.DictReader(input_file):
            matrix = np.array(
                [float(row[field]) for field in MATRIX_FIELDS]
            ).reshape(4, 4)
            poses.setdefault(row["pose"], []).append(
                {
                    "timestamp_ms": row["timestamp_ms"],
                    "frame_index": row["frame_index"],
                    "matrix": matrix,
                }
            )
    return poses


def _percentile(values: np.ndarray, percentile: int) -> float:
    return float(np.percentile(values, percentile))


def main() -> None:
    poses = _load_matrices()
    if "Neutral" not in poses or not poses["Neutral"]:
        raise ValueError("The recording must contain Neutral matrices.")
    neutral_matrix = np.mean(
        [item["matrix"] for item in poses["Neutral"]], axis=0
    )

    vector_rows: list[dict[str, object]] = []
    vectors_by_pose: dict[str, np.ndarray] = {}
    for pose_name, rows in poses.items():
        vectors = np.array(
            [
                _relative_rotation_vector(item["matrix"], neutral_matrix)
                for item in rows
            ]
        )
        vectors_by_pose[pose_name] = np.degrees(vectors)
        for item, vector in zip(rows, vectors_by_pose[pose_name]):
            vector_rows.append(
                {
                    "timestamp_ms": item["timestamp_ms"],
                    "pose": pose_name,
                    "frame_index": item["frame_index"],
                    "rotation_x_deg": f"{vector[0]:.6f}",
                    "rotation_y_deg": f"{vector[1]:.6f}",
                    "rotation_z_deg": f"{vector[2]:.6f}",
                    "rotation_magnitude_deg": f"{np.linalg.norm(vector):.6f}",
                }
            )

    with VECTORS_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=VECTOR_FIELDS)
        writer.writeheader()
        writer.writerows(vector_rows)

    report_lines = [
        "# Head Pose Axis and Sign Validation",
        "",
        "This report analyzes every matrix in `motion_frames.csv`. The Neutral "
        "reference is the mean of all recorded Neutral matrices.",
        "",
        "For each frame:",
        "",
        "```text",
        "R_relative = R_neutral.T @ R_current",
        "rotation_vector = log(R_relative)",
        "```",
        "",
        "The matrix scale is removed before calculating the relative rotation. "
        "Rotation-vector components are reported in degrees and are not named "
        "Yaw, Pitch, or Roll.",
        "",
        f"- Input matrices: `{sum(len(rows) for rows in poses.values())}`",
        f"- Output vectors: `{len(vector_rows)}`",
        f"- Per-frame vectors: `{VECTORS_PATH.name}`",
        "",
    ]

    for pose_name in ("Neutral", "Turn Left", "Turn Right", "Look Up", "Look Down"):
        if pose_name not in vectors_by_pose:
            continue
        vectors = vectors_by_pose[pose_name]
        medians = np.median(vectors, axis=0)
        p10 = np.array([_percentile(vectors[:, axis], 10) for axis in range(3)])
        p90 = np.array([_percentile(vectors[:, axis], 90) for axis in range(3)])
        report_lines.extend(
            [
                f"## {pose_name}",
                "",
                f"- Frames: `{len(vectors)}`",
                "",
                "| Component | Median (deg) | P10 (deg) | P90 (deg) |",
                "|---|---:|---:|---:|",
                f"| X | {medians[0]:+.2f} | {p10[0]:+.2f} | {p90[0]:+.2f} |",
                f"| Y | {medians[1]:+.2f} | {p10[1]:+.2f} | {p90[1]:+.2f} |",
                f"| Z | {medians[2]:+.2f} | {p10[2]:+.2f} | {p90[2]:+.2f} |",
                "",
            ]
        )
        if pose_name in EXPECTED_SIGN:
            axis, expected = EXPECTED_SIGN[pose_name]
            signs = vectors[:, axis] * expected > 0
            percentage = 100 * float(np.mean(signs))
            axis_name = "XYZ"[axis]
            direction = "positive" if expected > 0 else "negative"
            report_lines.append(
                f"- Expected sign: `{axis_name} {direction}`; preserved in "
                f"`{percentage:.2f}%` of frames."
            )
        else:
            report_lines.append(
                "- Expected sign: `N/A` for the Neutral reference."
            )
        report_lines.append("")

    OUTPUT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Analyzed {len(vector_rows)} recorded matrices.")
    print(f"Rotation vectors written to {VECTORS_PATH}")
    print(f"Validation report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
