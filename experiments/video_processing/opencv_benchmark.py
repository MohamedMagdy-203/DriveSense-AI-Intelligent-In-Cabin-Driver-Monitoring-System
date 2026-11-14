"""Benchmark webcam video capture, FPS, CPU usage, and RAM usage."""

import time

import cv2
import psutil


CAMERA_INDEX = 0
TEST_DURATION_SECONDS = 60
WINDOW_NAME = "OpenCV Webcam Benchmark"


def main() -> None:
    """Capture and display webcam frames until timeout or the user presses q."""
    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        print("Error: Could not open the laptop webcam.")
        return

    resolution = (
        int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    camera_fps = camera.get(cv2.CAP_PROP_FPS)
    print(f"Resolution: {resolution[0]}x{resolution[1]}")
    print(f"Camera FPS: {camera_fps:.2f}")

    process = psutil.Process()
    process.cpu_percent(interval=None)
    frame_count = 0
    cpu_samples = []
    ram_samples = []
    start_time = time.perf_counter()

    try:
        while time.perf_counter() - start_time < TEST_DURATION_SECONDS:
            success, frame = camera.read()
            if not success:
                print("Error: Could not capture a frame.")
                break

            frame_count += 1
            cpu_samples.append(process.cpu_percent(interval=None))
            ram_samples.append(process.memory_info().rss / (1024 * 1024))

            elapsed = time.perf_counter() - start_time
            current_fps = frame_count / elapsed if elapsed > 0 else 0.0
            cv2.putText(
                frame,
                f"FPS: {current_fps:.2f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.imshow(WINDOW_NAME, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    elapsed = time.perf_counter() - start_time
    average_fps = frame_count / elapsed if elapsed > 0 else 0.0
    average_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
    average_ram = sum(ram_samples) / len(ram_samples) if ram_samples else 0.0

    print(f"Test duration: {elapsed:.2f} seconds")
    print(f"Processed frames: {frame_count}")
    print(f"Average FPS: {average_fps:.2f}")
    print(f"Average CPU usage: {average_cpu:.2f}%")
    print(f"Average RAM usage: {average_ram:.2f} MB")


if __name__ == "__main__":
    main()
