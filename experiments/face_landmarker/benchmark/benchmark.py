"""Benchmark MediaPipe Face Landmarker with a webcam in live-stream mode."""

from __future__ import annotations

import argparse
import platform
import statistics
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
import psutil


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = ROOT / "models" / "face_landmarker.task"
DEFAULT_OUTPUT = Path(__file__).with_name("results.md")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
WINDOW_NAME = "MediaPipe Face Landmarker Benchmark"


@dataclass
class TrialResult:
    """Measurements collected during one webcam trial."""

    duration_seconds: float
    submitted_frames: int
    callback_frames: int
    detected_frames: int
    failed_detection_frames: int
    average_fps: float
    average_pipeline_latency_ms: float
    average_model_latency_ms: float
    average_cpu_percent: float
    average_ram_mb: float
    average_faces: float
    landmark_stability_percent: float
    mean_landmark_displacement: float
    resolution: str
    camera_fps: float


class CallbackState:
    """Thread-safe state shared by the live-stream result callback and loop."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.submitted_at: dict[int, float] = {}
        self.model_latencies: list[float] = []
        self.callback_frames = 0
        self.detected_frames = 0
        self.failed_detection_frames = 0
        self.face_counts: list[int] = []
        self.landmark_displacements: list[float] = []
        self.stable_landmarks = 0
        self.previous_landmarks: Optional[list[object]] = None

    def on_result(
        self,
        result: object,
        _output_image: object,
        timestamp_ms: int,
    ) -> None:
        received_at = time.perf_counter()
        with self.lock:
            submitted_at = self.submitted_at.pop(timestamp_ms, None)
            if submitted_at is not None:
                self.model_latencies.append((received_at - submitted_at) * 1000)

            faces = getattr(result, "face_landmarks", [])
            face_count = len(faces)
            self.callback_frames += 1
            self.face_counts.append(face_count)
            if face_count:
                self.detected_frames += 1
            else:
                self.failed_detection_frames += 1

            if face_count:
                current = list(faces[0])
                if self.previous_landmarks is not None:
                    displacement = _landmark_displacement(
                        self.previous_landmarks, current
                    )
                    self.landmark_displacements.append(displacement)
                    if displacement <= 0.02:
                        self.stable_landmarks += 1
                self.previous_landmarks = current


def _landmark_displacement(previous: list[object], current: list[object]) -> float:
    """Return mean normalized 3D displacement for corresponding landmarks."""
    count = min(len(previous), len(current))
    if not count:
        return 0.0
    distances = []
    for old, new in zip(previous[:count], current[:count]):
        dx = new.x - old.x
        dy = new.y - old.y
        dz = new.z - old.z
        distances.append((dx * dx + dy * dy + dz * dz) ** 0.5)
    return statistics.fmean(distances)


def _create_landmarker(model_path: Path, state: CallbackState):
    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(model_path),
        delegate=mp.tasks.BaseOptions.Delegate.CPU,
    )
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        result_callback=state.on_result,
    )
    return mp.tasks.vision.FaceLandmarker.create_from_options(options)


def run_trial(
    model_path: Path,
    camera_index: int,
    duration_seconds: float,
    display: bool,
    trial_number: int,
) -> TrialResult:
    """Run one trial and return measurements for model and pipeline separately."""
    state = CallbackState()
    landmarker = _create_landmarker(model_path, state)
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        landmarker.close()
        raise RuntimeError(f"Could not open webcam at index {camera_index}.")

    width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    camera_fps = camera.get(cv2.CAP_PROP_FPS)
    process = psutil.Process()
    process.cpu_percent(interval=None)
    cpu_samples: list[float] = []
    ram_samples: list[float] = []
    pipeline_latencies: list[float] = []
    submitted_frames = 0
    started = time.perf_counter()
    print(f"CPU trial {trial_number}: {width}x{height}")

    try:
        while time.perf_counter() - started < duration_seconds:
            pipeline_started = time.perf_counter()
            success, frame = camera.read()
            if not success:
                raise RuntimeError("The webcam stopped returning frames.")

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((time.perf_counter() - started) * 1000)
            with state.lock:
                state.submitted_at[timestamp_ms] = time.perf_counter()
            landmarker.detect_async(image, timestamp_ms)
            submitted_frames += 1

            cpu_samples.append(process.cpu_percent(interval=None))
            ram_samples.append(process.memory_info().rss / (1024 * 1024))
            if display:
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            pipeline_latencies.append((time.perf_counter() - pipeline_started) * 1000)
    finally:
        camera.release()
        landmarker.close()
        if display:
            cv2.destroyAllWindows()

    # Allow callbacks already queued by the task runner to be included.
    callback_deadline = time.perf_counter() + 2.0
    while time.perf_counter() < callback_deadline:
        with state.lock:
            pending = len(state.submitted_at)
        if not pending:
            break
        time.sleep(0.01)

    elapsed = time.perf_counter() - started
    with state.lock:
        callback_frames = state.callback_frames
        detected_frames = state.detected_frames
        failed_detection_frames = state.failed_detection_frames
        average_faces = (
            statistics.fmean(state.face_counts) if state.face_counts else 0.0
        )
        model_latency = (
            statistics.fmean(state.model_latencies)
            if state.model_latencies
            else 0.0
        )
        displacement = (
            statistics.fmean(state.landmark_displacements)
            if state.landmark_displacements
            else 0.0
        )
        stability = (
            100 * state.stable_landmarks / len(state.landmark_displacements)
            if state.landmark_displacements
            else 0.0
        )

    return TrialResult(
        duration_seconds=elapsed,
        submitted_frames=submitted_frames,
        callback_frames=callback_frames,
        detected_frames=detected_frames,
        failed_detection_frames=failed_detection_frames,
        average_fps=submitted_frames / elapsed if elapsed else 0.0,
        average_pipeline_latency_ms=(
            statistics.fmean(pipeline_latencies) if pipeline_latencies else 0.0
        ),
        average_model_latency_ms=model_latency,
        average_cpu_percent=statistics.fmean(cpu_samples) if cpu_samples else 0.0,
        average_ram_mb=statistics.fmean(ram_samples) if ram_samples else 0.0,
        average_faces=average_faces,
        landmark_stability_percent=stability,
        mean_landmark_displacement=displacement,
        resolution=f"{width}x{height}",
        camera_fps=camera_fps,
    )


def _average(results: list[TrialResult], field: str) -> float:
    return statistics.fmean(getattr(result, field) for result in results)


def _render_report(
    results: list[TrialResult],
    model_path: Path,
    duration_seconds: float,
    trials: int,
) -> str:
    lines = [
        "# MediaPipe Face Landmarker Benchmark Results",
        "",
        "Generated by `face_landmarker_benchmark.py`.",
        "",
        "## Configuration",
        f"- Model: `{model_path}`",
        f"- Duration per trial: `{duration_seconds:.0f} seconds`",
        f"- CPU trials: `{trials}`",
        "- Running mode: `LIVE_STREAM`",
        "- Face count: `1` (enables MediaPipe tracking/smoothing)",
        f"- OS: `{platform.platform()}`",
        f"- CPU: `{platform.processor() or 'Unknown'}`",
        "",
        "Model latency is measured from `detect_async` submission until the "
        "result callback. Pipeline latency includes capture, color conversion, "
        "submission, and optional display. Asynchronous callbacks that did not "
        "arrive before the 2-second drain are not included in model latency.",
        "",
    ]
    lines.extend(
        [
            "## CPU",
            "",
            "| Trial | Duration (s) | Submitted frames | Callback frames | "
            "FPS | Model latency (ms) | Pipeline latency (ms) | "
            "CPU (%) | RAM (MB) | Detected frames | Failed detection frames | "
            "Avg faces | Landmark stability (%) |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, result in enumerate(results, 1):
        lines.append(
            f"| {index} | {result.duration_seconds:.2f} | "
            f"{result.submitted_frames} | {result.callback_frames} | "
            f"{result.average_fps:.2f} | {result.average_model_latency_ms:.2f} | "
            f"{result.average_pipeline_latency_ms:.2f} | "
            f"{result.average_cpu_percent:.2f} | {result.average_ram_mb:.2f} | "
            f"{result.detected_frames} | {result.failed_detection_frames} | "
            f"{result.average_faces:.2f} | "
            f"{result.landmark_stability_percent:.2f} |"
        )
    lines.extend(
        [
            "",
            "**Three-trial average**",
            "",
            f"- FPS: `{_average(results, 'average_fps'):.2f}`",
            f"- Model latency: `{_average(results, 'average_model_latency_ms'):.2f} ms`",
            f"- Pipeline latency: `{_average(results, 'average_pipeline_latency_ms'):.2f} ms`",
            f"- CPU: `{_average(results, 'average_cpu_percent'):.2f}%`",
            f"- RAM: `{_average(results, 'average_ram_mb'):.2f} MB`",
            f"- Face detection rate: `{100 * _average(results, 'detected_frames') / max(_average(results, 'callback_frames'), 1):.2f}%`",
            f"- Failed detection frames (average): `{_average(results, 'failed_detection_frames'):.2f}`",
            f"- Landmark stability: `{_average(results, 'landmark_stability_percent'):.2f}%`",
            f"- Mean landmark displacement: `{_average(results, 'mean_landmark_displacement'):.5f}`",
            f"- Camera: `{results[0].resolution}` at approximately "
            f"`{results[0].camera_fps:.2f} FPS`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable the OpenCV preview window.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.model.is_file():
        raise FileNotFoundError(
            f"Model not found: {args.model}. Download it from {MODEL_URL} "
            f"and save it as {args.model}."
        )
    if args.duration <= 0 or args.trials <= 0:
        raise ValueError("--duration and --trials must be greater than zero.")

    results = [
        run_trial(
            args.model,
            args.camera,
            args.duration,
            not args.no_display,
            trial_number,
        )
        for trial_number in range(1, args.trials + 1)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        _render_report(results, args.model, args.duration, args.trials),
        encoding="utf-8",
    )
    print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()