# Phone Detection Experiment

This experiment runs the trained YOLO11n phone detector on a live webcam.
It performs object detection only; it does not classify phone-use behavior.

## Requirements

- The trained checkpoint at
  `artifacts/phone_detection/weights/best.pt`.
- A webcam accessible to Windows.
- CUDA-enabled PyTorch, Ultralytics, and OpenCV in the selected Python
  environment.

## Run

From the repository root in WSL, using the Windows Python environment:

```bash
WIN_ROOT=$(wslpath -w "$PWD")
./.venv/Scripts/python.exe "$WIN_ROOT/experiments/phone_detection/live.py"
```

The script requires CUDA and uses GPU 0. It displays the detected phone boxes,
confidence scores, current GPU, inference FPS, and detection count. Press `Q`
or `Esc` to close the live window.

The camera index, image size, and confidence threshold are constants at the top
of `live.py`. The script does not save or modify camera frames.
