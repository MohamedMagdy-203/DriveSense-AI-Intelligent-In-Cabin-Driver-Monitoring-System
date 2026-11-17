"""Inspect Face Landmarker facial transformation matrices."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import cv2
import numpy as np

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

OUTPUT_PATH = Path(__file__).with_name("results.md")
DURATION_SECONDS = 10


def main() -> None:
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")

    matrix: np.ndarray | None = None
    matrix_count = 0
    frame_count = 0
    timestamp_ms = int(time.perf_counter() * 1000)
    started = time.perf_counter()
    try:
        with create_landmarker() as landmarker:
            while time.perf_counter() - started < DURATION_SECONDS:
                frame = read_gstreamer_frame(process.stdout)
                if frame is None:
                    raise RuntimeError("GStreamer stopped returning frames.")
                frame_count += 1
                timestamp_ms += 1
                result = landmarker.detect_for_video(
                    face_image(frame), timestamp_ms
                )
                if result.facial_transformation_matrixes:
                    matrix_count = len(result.facial_transformation_matrixes)
                    if matrix is None:
                        matrix = np.asarray(
                            result.facial_transformation_matrixes[0]
                        )
                cv2.putText(
                    frame,
                    f"Matrices: {matrix_count} | Q/Esc: exit",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        stop_gstreamer(process)
        cv2.destroyAllWindows()

    if matrix is None:
        raise RuntimeError("No facial transformation matrix was produced.")

    values = np.array2string(matrix, precision=6, suppress_small=False)
    report = f"""# Facial Transformation Matrix Inspection

- Capture duration: `{DURATION_SECONDS} seconds`
- Processed frames: `{frame_count}`
- Matrices reported for the latest detected face: `{matrix_count}`
- First matrix shape: `{matrix.shape}`

## First matrix values

```text
{values}
```

The matrix is recorded for axis and sign validation. Yaw, pitch, and roll are
not calculated until the coordinate convention is verified.
"""
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
