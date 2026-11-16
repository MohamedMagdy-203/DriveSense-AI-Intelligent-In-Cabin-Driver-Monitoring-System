## MediaPipe CPU Pipeline Comparison

3 trials were run for each capture pipeline under the same conditions, with 60 seconds per trial: 640x480 webcam input, MediaPipe Face Landmarker CPU, one face, and no display window.

- Duration per trial: `60 seconds`
- Trials per pipeline: `3`
- Model: `models/face_landmarker.task`
- MediaPipe: CPU delegate

### OpenCV + MediaPipe

| Trial | Duration (s) | Frames | FPS | Inference latency (ms) | CPU (%) | RAM (MB) | Detection rate (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 60.59 | 1690 | 27.89 | 11.28 | 68.20 | 185.65 | 99.53 |
| 2 | 60.77 | 1781 | 29.31 | 9.91 | 67.98 | 161.38 | 93.54 |
| 3 | 60.49 | 1787 | 29.54 | 9.74 | 63.82 | 160.14 | 100.00 |

**3-trial average**

- FPS: `28.91`
- Inference latency: `10.31 ms`
- CPU: `66.67%`
- RAM: `169.06 MB`
- Detection rate: `97.66%`

### GStreamer + MediaPipe

| Trial | Duration (s) | Frames | FPS | Inference latency (ms) | CPU (%) | RAM (MB) | Detection rate (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 60.49 | 1780 | 29.43 | 9.08 | 51.92 | 142.25 | 100.00 |
| 2 | 60.49 | 1780 | 29.43 | 9.51 | 53.64 | 136.20 | 98.54 |
| 3 | 60.50 | 1779 | 29.40 | 9.39 | 51.22 | 151.63 | 97.81 |

**3-trial average**

- FPS: `29.42`
- Inference latency: `9.33 ms`
- CPU: `52.26%`
- RAM: `143.36 MB`
- Detection rate: `98.78%`
