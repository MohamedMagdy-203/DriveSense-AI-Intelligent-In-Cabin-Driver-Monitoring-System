"""Live demo for the head pose estimation module."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import cv2

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from drivesense.face.runtime import (
    WINDOW_NAME,
    create_landmarker,
    face_image,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)
from drivesense.head_pose.pose import HeadPoseEstimator, HeadPoseStatus
from drivesense.head_pose.temporal import HeadPoseTemporalAnalyzer


def main() -> None:
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")

    estimator = HeadPoseEstimator()
    temporal = HeadPoseTemporalAnalyzer(window_seconds=2.0)
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
                estimate = estimator.update(result)
                temporal_state = temporal.update(estimate)
                cv2.putText(
                    frame,
                    f"Head pose: {estimate.status.value}",
                    (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 0) if estimate.status is HeadPoseStatus.OK
                    else (0, 0, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"History (2s): {len(temporal_state.history)} valid samples",
                    (10, 180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                if estimate.status is HeadPoseStatus.OK:
                    vector = estimate.rotation_vector_degrees
                    if vector is None or estimate.magnitude_deg is None:
                        raise RuntimeError(
                            "Head pose returned OK without rotation values."
                        )
                    cv2.putText(
                        frame,
                        f"Rotation vector: [{vector[0]:+.1f}, "
                        f"{vector[1]:+.1f}, {vector[2]:+.1f}] deg",
                        (10, 75),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (255, 255, 255),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"Magnitude: {estimate.magnitude_deg:.1f} deg",
                        (10, 110),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (255, 255, 255),
                        2,
                    )
                cv2.putText(
                    frame,
                    "Q/Esc: exit | Neutral is calibrated on first valid frame",
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
