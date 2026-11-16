"""Compare OpenCV and GStreamer capture pipelines with MediaPipe CPU inference."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import psutil


ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT / "models" / "face_landmarker.task"
WIDTH = 640
HEIGHT = 480
CAMERA_INDEX = 0


@dataclass
class TrialResult:
    pipeline: str
    duration_seconds: float
    frames: int
    detected_frames: int
    fps: float
    inference_latency_ms: float
    cpu_percent: float
    ram_mb: float


def _create_landmarker():
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH),
            delegate=mp.tasks.BaseOptions.Delegate.CPU,
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return mp.tasks.vision.FaceLandmarker.create_from_options(options)


def _sample_process_resources(process: psutil.Process) -> tuple[float, float]:
    processes = [process, *process.children(recursive=True)]
    cpu = 0.0
    ram = 0.0
    for child in processes:
        try:
            cpu += child.cpu_percent(interval=None)
            ram += child.memory_info().rss / (1024 * 1024)
        except psutil.NoSuchProcess:
            continue
    return cpu, ram


def _detect(landmarker, frame, timestamp_ms: int):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    started = time.perf_counter()
    result = landmarker.detect_for_video(image, timestamp_ms)
    return result, (time.perf_counter() - started) * 1000


def _run_opencv_trial(duration: float, trial_number: int) -> TrialResult:
    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam with OpenCV.")

    return _run_frame_trial(
        "OpenCV",
        duration,
        trial_number,
        lambda: camera.read(),
        lambda: camera.release(),
    )


def _start_gstreamer():
    gst_launch = shutil.which("gst-launch-1.0")
    if gst_launch is None:
        candidate = Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "gst-launch-1.0.exe"
        if candidate.is_file():
            gst_launch = str(candidate)
    if gst_launch is None:
        raise RuntimeError("Could not find gst-launch-1.0.")

    pipeline = [
        gst_launch,
        "-q",
        "ksvideosrc",
        f"device-index={CAMERA_INDEX}",
        "!",
        "videoconvert",
        "!",
        "videoscale",
        "!",
        f"video/x-raw,format=BGR,width={WIDTH},height={HEIGHT}",
        "!",
        "fdsink",
        "fd=1",
    ]
    return subprocess.Popen(
        pipeline,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )


def _read_frame(stream, frame_size: int):
    data = bytearray()
    while len(data) < frame_size:
        chunk = stream.read(frame_size - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))


def _run_gstreamer_trial(duration: float, trial_number: int) -> TrialResult:
    process = _start_gstreamer()
    if process.stdout is None:
        process.kill()
        raise RuntimeError("Could not read GStreamer frames.")

    frame_size = WIDTH * HEIGHT * 3
    try:
        return _run_frame_trial(
            "GStreamer",
            duration,
            trial_number,
            lambda: (
                (True, frame)
                if (frame := _read_frame(process.stdout, frame_size)) is not None
                else (False, None)
            ),
            lambda: _stop_gstreamer(process),
        )
    finally:
        _stop_gstreamer(process)


def _stop_gstreamer(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def _run_frame_trial(
    pipeline: str,
    duration: float,
    trial_number: int,
    read_frame,
    close_source,
) -> TrialResult:
    process = psutil.Process()
    process.cpu_percent(interval=None)
    _sample_process_resources(process)
    frames = 0
    detected_frames = 0
    latencies: list[float] = []
    cpu_samples: list[float] = []
    ram_samples: list[float] = []
    started = time.perf_counter()

    print(f"{pipeline} + MediaPipe trial {trial_number}: {WIDTH}x{HEIGHT}")
    try:
        with _create_landmarker() as landmarker:
            while time.perf_counter() - started < duration:
                success, frame = read_frame()
                if not success:
                    raise RuntimeError(f"{pipeline} stopped returning frames.")
                result, latency = _detect(
                    landmarker,
                    frame,
                    int((time.perf_counter() - started) * 1000),
                )
                frames += 1
                detected_frames += int(bool(result.face_landmarks))
                latencies.append(latency)
                cpu, ram = _sample_process_resources(process)
                cpu_samples.append(cpu)
                ram_samples.append(ram)
    finally:
        close_source()

    elapsed = time.perf_counter() - started
    return TrialResult(
        pipeline=pipeline,
        duration_seconds=elapsed,
        frames=frames,
        detected_frames=detected_frames,
        fps=frames / elapsed if elapsed else 0.0,
        inference_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        cpu_percent=sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
        ram_mb=sum(ram_samples) / len(ram_samples) if ram_samples else 0.0,
    )


def _average(results: list[TrialResult], field: str) -> float:
    return sum(getattr(result, field) for result in results) / len(results)


def _report(results: dict[str, list[TrialResult]], duration: float, trials: int) -> str:
    lines = [
        "## MediaPipe CPU Pipeline Comparison",
        "",
        f"{trials} trials were run for each capture pipeline under the same "
        f"conditions, with {duration:.0f} seconds per trial: 640x480 webcam "
        "input, MediaPipe Face Landmarker CPU, one face, and no display window.",
        "",
        f"- Duration per trial: `{duration:.0f} seconds`",
        f"- Trials per pipeline: `{trials}`",
        "- Model: `models/face_landmarker.task`",
        "- MediaPipe: CPU delegate",
        "",
    ]
    for pipeline, pipeline_results in results.items():
        lines.extend(
            [
                f"### {pipeline} + MediaPipe",
                "",
                "| Trial | Duration (s) | Frames | FPS | Inference latency (ms) | CPU (%) | RAM (MB) | Detection rate (%) |",
                "|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for index, result in enumerate(pipeline_results, 1):
            lines.append(
                f"| {index} | {result.duration_seconds:.2f} | {result.frames} | "
                f"{result.fps:.2f} | {result.inference_latency_ms:.2f} | "
                f"{result.cpu_percent:.2f} | {result.ram_mb:.2f} | "
                f"{100 * result.detected_frames / max(result.frames, 1):.2f} |"
            )
        lines.extend(
            [
                "",
                f"**{trials}-trial average**",
                "",
                f"- FPS: `{_average(pipeline_results, 'fps'):.2f}`",
                f"- Inference latency: `{_average(pipeline_results, 'inference_latency_ms'):.2f} ms`",
                f"- CPU: `{_average(pipeline_results, 'cpu_percent'):.2f}%`",
                f"- RAM: `{_average(pipeline_results, 'ram_mb'):.2f} MB`",
                f"- Detection rate: `{100 * _average(pipeline_results, 'detected_frames') / max(_average(pipeline_results, 'frames'), 1):.2f}%`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("mediapipe_pipeline_results.md"),
    )
    args = parser.parse_args()
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    if args.duration <= 0 or args.trials <= 0:
        raise ValueError("--duration and --trials must be greater than zero.")

    results = {"OpenCV": [], "GStreamer": []}
    for pipeline, runner in (
        ("OpenCV", _run_opencv_trial),
        ("GStreamer", _run_gstreamer_trial),
    ):
        for trial_number in range(1, args.trials + 1):
            results[pipeline].append(runner(args.duration, trial_number))

    args.output.write_text(
        _report(results, args.duration, args.trials),
        encoding="utf-8",
    )
    print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()
