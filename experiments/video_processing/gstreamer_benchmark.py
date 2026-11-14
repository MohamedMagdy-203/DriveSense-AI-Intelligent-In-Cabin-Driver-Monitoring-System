"""Benchmark GStreamer webcam capture, FPS, CPU usage, and RAM usage."""

import os
import re
import shutil
import subprocess
import time

import psutil


CAMERA_INDEX = 0
TEST_DURATION_SECONDS = 60
WIDTH = 640
HEIGHT = 480

FPS_PATTERN = re.compile(r"Updated (?:min|max)-fps to ([\d.]+)")


def main() -> None:
    """Run the GStreamer webcam pipeline until the benchmark timeout."""
    gst_launch = shutil.which("gst-launch-1.0")
    if gst_launch is None:
        raise RuntimeError("Could not find gst-launch-1.0 on PATH.")

    pipeline = [
        gst_launch,
        "-e",
        "ksvideosrc",
        f"device-index={CAMERA_INDEX}",
        "!",
        "videoconvert",
        "!",
        "videoscale",
        "!",
        f"video/x-raw,width={WIDTH},height={HEIGHT}",
        "!",
        "fpsdisplaysink",
        "text-overlay=false",
        "sync=false",
        "silent=false",
        "fps-update-interval=1000",
    ]

    environment = {"GST_DEBUG": "fpsdisplaysink:6"}
    process = subprocess.Popen(
        pipeline,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, **environment},
    )
    process_monitor = psutil.Process(process.pid)
    process_monitor.cpu_percent(interval=None)
    cpu_samples = []
    ram_samples = []
    output = []
    start_time = time.perf_counter()

    try:
        while time.perf_counter() - start_time < TEST_DURATION_SECONDS:
            if process.poll() is not None:
                break

            try:
                cpu_samples.append(process_monitor.cpu_percent(interval=0.5))
                ram_samples.append(process_monitor.memory_info().rss / (1024 * 1024))
            except psutil.NoSuchProcess:
                break
    finally:
        if process.poll() is None:
            process.terminate()

        process_output, _ = process.communicate(timeout=10)
        output.append(process_output)

    elapsed = time.perf_counter() - start_time
    if process.returncode not in (0, 1, -15):
        details = "".join(output).strip()
        raise RuntimeError(
            f"GStreamer pipeline exited with code {process.returncode}.\n{details}"
        )

    log = "".join(output)
    fps_values = [float(value) for value in FPS_PATTERN.findall(log)]
    average_fps = sum(fps_values) / len(fps_values) if fps_values else 0.0
    frame_count = round(average_fps * elapsed)

    average_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
    average_ram = sum(ram_samples) / len(ram_samples) if ram_samples else 0.0

    print(f"Test duration: {elapsed:.2f} seconds")
    print(f"Processed frames: {frame_count}")
    print(f"Average FPS: {average_fps:.2f}")
    print(f"Average CPU usage: {average_cpu:.2f}%")
    print(f"Average RAM usage: {average_ram:.2f} MB")


if __name__ == "__main__":
    main()
