"""Display and inspect MediaPipe face landmarks with EAR values."""

from __future__ import annotations

import time
import sys
from pathlib import Path

if __package__ in (None, ""):
    script_directory = str(Path(__file__).resolve().parent)
    if script_directory in sys.path:
        sys.path.remove(script_directory)
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import cv2

from drivesense.face.runtime import (
    EAR_POINTS,
    EYE_GROUPS,
    LEFT_EYE_INDICES,
    RIGHT_EYE_INDICES,
    WINDOW_NAME,
    create_landmarker,
    draw_landmark,
    eye_aspect_ratio,
    face_image,
    print_landmark_output,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)

EAR_CLOSED_THRESHOLD = 0.15
PROLONGED_CLOSURE_MS = 500


def main() -> None:
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")

    timestamp_ms = int(time.perf_counter() * 1000)
    closure_started_ms: int | None = None
    printed_output = False

    try:
        with create_landmarker() as landmarker:
            while True:
                frame = read_gstreamer_frame(process.stdout)
                if frame is None:
                    raise RuntimeError("GStreamer stopped returning frames.")
                timestamp_ms = max(timestamp_ms + 1, int(time.perf_counter() * 1000))
                result = landmarker.detect_for_video(
                    face_image(frame), timestamp_ms
                )

                if result.face_landmarks:
                    face_landmarks = result.face_landmarks[0]
                    if not printed_output:
                        print_landmark_output(face_landmarks)
                        printed_output = True
                    right_ear = eye_aspect_ratio(
                        face_landmarks, EAR_POINTS["right_eye"]
                    )
                    left_ear = eye_aspect_ratio(
                        face_landmarks, EAR_POINTS["left_eye"]
                    )
                    average_ear = (right_ear + left_ear) / 2
                    if average_ear < EAR_CLOSED_THRESHOLD:
                        closure_started_ms = (
                            timestamp_ms
                            if closure_started_ms is None
                            else closure_started_ms
                        )
                        closure_duration_ms = timestamp_ms - closure_started_ms
                        status = (
                            "PROLONGED CLOSURE"
                            if closure_duration_ms >= PROLONGED_CLOSURE_MS
                            else "CLOSED"
                        )
                    else:
                        closure_started_ms = None
                        closure_duration_ms = 0
                        status = "OPEN"

                    for index in RIGHT_EYE_INDICES:
                        draw_landmark(frame, index, face_landmarks[index], (0, 255, 255))
                    for index in LEFT_EYE_INDICES:
                        draw_landmark(frame, index, face_landmarks[index], (255, 255, 0))

                    for y, text, color in (
                        (60, f"Right Eye EAR: {right_ear:.3f}", (0, 255, 255)),
                        (90, f"Left Eye EAR: {left_ear:.3f}", (255, 255, 0)),
                        (120, f"Average EAR: {average_ear:.3f}", (255, 255, 255)),
                        (155, f"Eye status: {status}",
                         (0, 255, 0) if status == "OPEN" else (0, 0, 255)),
                    ):
                        cv2.putText(frame, text, (10, y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
                    if closure_started_ms is not None:
                        cv2.putText(frame, f"Closure: {closure_duration_ms} ms",
                                    (10, 185), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.65, (0, 0, 255), 2)

                cv2.putText(frame, "Yellow: right eye | Cyan: left eye | Q/Esc: exit",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                            (255, 255, 255), 2)
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        stop_gstreamer(process)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
