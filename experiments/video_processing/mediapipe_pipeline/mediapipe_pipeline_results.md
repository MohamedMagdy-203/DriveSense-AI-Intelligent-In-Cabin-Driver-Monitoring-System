## MediaPipe CPU Pipeline Comparison

3 trials were run for each capture pipeline under the same conditions, with 60 seconds per trial: 640x480 webcam input, MediaPipe Face Landmarker CPU, one face, and no display window.

- Duration per trial: `60 seconds`
- Trials per pipeline: `3`
- Model: `models/face_landmarker.task`
- MediaPipe: CPU delegate

### OpenCV + MediaPipe

| Trial | Duration (s) | Frames | FPS | Inference latency (ms) | CPU (%) | RAM (MB) | Detection rate (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 60.57 | 1778 | 29.36 | 9.52 | 63.94 | 186.11 | 100.00 |
| 2 | 60.53 | 1787 | 29.52 | 9.38 | 65.43 | 191.58 | 100.00 |
| 3 | 60.49 | 1787 | 29.54 | 9.22 | 61.80 | 172.45 | 100.00 |

**3-trial average**

- FPS: `29.47`
- Inference latency: `9.37 ms`
- CPU: `63.72%`
- RAM: `183.38 MB`
- Detection rate: `100.00%`

### GStreamer + MediaPipe

| Trial | Duration (s) | Frames | FPS | Inference latency (ms) | CPU (%) | RAM (MB) | Detection rate (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 60.50 | 1780 | 29.42 | 8.73 | 49.47 | 138.90 | 99.78 |
| 2 | 60.49 | 1778 | 29.39 | 8.72 | 50.25 | 131.32 | 99.89 |
| 3 | 60.50 | 1768 | 29.22 | 9.60 | 54.12 | 128.45 | 100.00 |

**3-trial average**

- FPS: `29.35`
- Inference latency: `9.02 ms`
- CPU: `51.28%`
- RAM: `132.89 MB`
- Detection rate: `99.89%`
