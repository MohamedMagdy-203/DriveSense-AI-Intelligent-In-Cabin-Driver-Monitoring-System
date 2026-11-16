"""Monitor eye closure using per-frame EAR and timestamp duration."""

from __future__ import annotations

import csv
from datetime import datetime
from collections import deque
import time
import sys
from pathlib import Path

import cv2

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from experiments.face_landmarker.common.runtime import (
    EAR_POINTS,
    WINDOW_NAME,
    create_landmarker,
    eye_aspect_ratio,
    eye_openness,
    face_image,
    read_gstreamer_frame,
    start_gstreamer,
    stop_gstreamer,
)

EAR_CLOSED_THRESHOLD = 0.15
PROLONGED_CLOSURE_MS = 500
PERCLOS_CLOSURE_SCORE_THRESHOLD = 0.8
PERCLOS_BLINK_EXCLUSION_MS = 200
PERCLOS_WINDOW_MS = 60_000
# Baselines measured by the latest three-phase calibration run.
OPENNESS_OPEN_BASELINE = 0.3298
OPENNESS_CLOSED_BASELINE = 0.0736
EVENTS_PATH = Path(__file__).with_name("events.csv")
EVENT_FIELDS = [
    "timestamp",
    "event_type",
    "duration_ms",
    "right_ear",
    "left_ear",
    "perclos_60s",
]


class PerclosWindow:
    """Track closed and observed durations over a rolling time window."""

    def __init__(self, window_ms: int) -> None:
        self.window_ms = window_ms
        self.segments: deque[tuple[int, int, bool]] = deque()
        self.last_timestamp_ms: int | None = None
        self.last_closed: bool | None = None

    def update(self, timestamp_ms: int, closed: bool | None) -> float:
        if (
            closed is not None
            and self.last_timestamp_ms is not None
            and self.last_closed is not None
            and timestamp_ms > self.last_timestamp_ms
        ):
            self.segments.append(
                (self.last_timestamp_ms, timestamp_ms, self.last_closed)
            )

        if closed is None:
            self.last_timestamp_ms = None
            self.last_closed = None
        else:
            self.last_timestamp_ms = timestamp_ms
            self.last_closed = closed

        window_start = timestamp_ms - self.window_ms
        while self.segments and self.segments[0][1] <= window_start:
            self.segments.popleft()

        closed_duration = 0
        observed_duration = 0
        for start_ms, end_ms, was_closed in self.segments:
            clipped_start = max(start_ms, window_start)
            if end_ms <= clipped_start:
                continue
            duration = end_ms - clipped_start
            observed_duration += duration
            if was_closed:
                closed_duration += duration

        if observed_duration == 0:
            return 0.0
        return 100 * closed_duration / observed_duration


def _create_event_log():
    file_exists = EVENTS_PATH.is_file() and EVENTS_PATH.stat().st_size > 0
    if file_exists:
        with EVENTS_PATH.open(newline="", encoding="utf-8") as existing_file:
            reader = csv.DictReader(existing_file)
            if "perclos_60s" not in (reader.fieldnames or []):
                historical_rows = list(reader)
                with EVENTS_PATH.open("w", newline="", encoding="utf-8") as migrated:
                    writer = csv.DictWriter(migrated, fieldnames=EVENT_FIELDS)
                    writer.writeheader()
                    for row in historical_rows:
                        row["perclos_60s"] = ""
                        writer.writerow(row)
    log_file = EVENTS_PATH.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(log_file, fieldnames=EVENT_FIELDS)
    if not file_exists:
        writer.writeheader()
        log_file.flush()
    return log_file, writer


def _closure_score(openness: float) -> float:
    baseline_range = OPENNESS_OPEN_BASELINE - OPENNESS_CLOSED_BASELINE
    if baseline_range <= 0:
        raise ValueError("Open and closed openness baselines must be ordered.")
    return min(
        1.0,
        max(
            0.0,
            (OPENNESS_OPEN_BASELINE - openness) / baseline_range,
        ),
    )


def main() -> None:
    process = start_gstreamer()
    if process.stdout is None:
        stop_gstreamer(process)
        raise RuntimeError("Could not read frames from GStreamer.")
    timestamp_ms = int(time.perf_counter() * 1000)
    closure_started_ms: int | None = None
    prolonged_closure_recorded = False
    normal_blinks = 0
    prolonged_closures = 0
    blink_durations: list[int] = []
    closure_durations: list[int] = []
    right_ear_samples: list[float] = []
    left_ear_samples: list[float] = []
    closure_started_at: str | None = None
    perclos_closure_started_ms: int | None = None
    perclos_percent = 0.0
    perclos = PerclosWindow(PERCLOS_WINDOW_MS)
    log_file, event_writer = _create_event_log()

    def record_closure(end_timestamp_ms: int) -> None:
        nonlocal normal_blinks, prolonged_closures
        if closure_started_ms is None or closure_started_at is None:
            return
        duration_ms = end_timestamp_ms - closure_started_ms
        is_prolonged = duration_ms >= PROLONGED_CLOSURE_MS
        event_type = "Prolonged Closure" if is_prolonged else "Normal Blink"
        event_writer.writerow(
            {
                "timestamp": closure_started_at,
                "event_type": event_type,
                "duration_ms": duration_ms,
                "right_ear": (
                    f"{sum(right_ear_samples) / len(right_ear_samples):.4f}"
                    if right_ear_samples
                    else ""
                ),
                "left_ear": (
                    f"{sum(left_ear_samples) / len(left_ear_samples):.4f}"
                    if left_ear_samples
                    else ""
                ),
                "perclos_60s": f"{perclos_percent:.2f}",
            }
        )
        log_file.flush()
        closure_durations.append(duration_ms)
        if is_prolonged:
            prolonged_closures += 1
        else:
            normal_blinks += 1
            blink_durations.append(duration_ms)
        right_ear_samples.clear()
        left_ear_samples.clear()
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
                    face = result.face_landmarks[0]
                    average_ear = (
                        eye_aspect_ratio(face, EAR_POINTS["right_eye"])
                        + eye_aspect_ratio(face, EAR_POINTS["left_eye"])
                    ) / 2
                    openness = (
                        eye_openness(face, EAR_POINTS["right_eye"])
                        + eye_openness(face, EAR_POINTS["left_eye"])
                    ) / 2
                    closure_score = _closure_score(openness)
                    if average_ear < EAR_CLOSED_THRESHOLD:
                        if closure_started_ms is None:
                            closure_started_ms = timestamp_ms
                            closure_started_at = datetime.now().astimezone().isoformat()
                            right_ear_samples.clear()
                            left_ear_samples.clear()
                        right_ear_samples.append(
                            eye_aspect_ratio(face, EAR_POINTS["right_eye"])
                        )
                        left_ear_samples.append(
                            eye_aspect_ratio(face, EAR_POINTS["left_eye"])
                        )
                        duration_ms = timestamp_ms - closure_started_ms
                        status = (
                            "PROLONGED CLOSURE"
                            if duration_ms >= PROLONGED_CLOSURE_MS
                            else "CLOSED"
                        )
                        prolonged_closure_recorded = (
                            duration_ms >= PROLONGED_CLOSURE_MS
                        )
                    else:
                        record_closure(timestamp_ms)
                        closure_started_ms = None
                        closure_started_at = None
                        prolonged_closure_recorded = False
                        duration_ms = 0
                        status = "OPEN"
                    perclos_percent = perclos.update(
                        timestamp_ms,
                        (
                            closure_score >= PERCLOS_CLOSURE_SCORE_THRESHOLD
                            and perclos_closure_started_ms is not None
                            and timestamp_ms - perclos_closure_started_ms
                            > PERCLOS_BLINK_EXCLUSION_MS
                        ),
                    )
                    if closure_score >= PERCLOS_CLOSURE_SCORE_THRESHOLD:
                        if perclos_closure_started_ms is None:
                            perclos_closure_started_ms = timestamp_ms
                    else:
                        perclos_closure_started_ms = None
                    color = (0, 255, 0) if status == "OPEN" else (0, 0, 255)
                    cv2.putText(frame, f"Average EAR: {average_ear:.3f}",
                                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (255, 255, 255), 2)
                    cv2.putText(frame, f"Closure score: {closure_score:.3f}",
                                (10, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (255, 255, 255), 2)
                    cv2.putText(frame, f"Eye status: {status}", (10, 95),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    if closure_started_ms is not None:
                        cv2.putText(frame, f"Closure: {duration_ms} ms",
                                    (10, 130), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.7, color, 2)
                    cv2.putText(
                        frame,
                        f"Normal blinks: {normal_blinks}",
                        (10, 165),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"Prolonged closures: {prolonged_closures}",
                        (10, 200),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"PERCLOS (60s): {perclos_percent:.1f}%",
                        (10, 235),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 165, 0),
                        2,
                    )
                else:
                    perclos_closure_started_ms = None
                    perclos_percent = perclos.update(timestamp_ms, None)
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        record_closure(timestamp_ms)
        log_file.close()
        stop_gstreamer(process)
        cv2.destroyAllWindows()

    print("\nSession summary")
    print(f"Total blinks: {normal_blinks}")
    print(f"Total prolonged closures: {prolonged_closures}")
    print(
        "Average blink duration: "
        f"{sum(blink_durations) / len(blink_durations):.2f} ms"
        if blink_durations
        else "Average blink duration: 0.00 ms"
    )
    print(
        f"Longest eye closure: {max(closure_durations, default=0)} ms"
    )
    print(f"Events written to: {EVENTS_PATH}")


if __name__ == "__main__":
    main()
