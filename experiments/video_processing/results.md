# Video Processing Benchmark Results

## Experiment 01: OpenCV Webcam Capture

### Environment
- CPU: Intel Core i5-10500H
- RAM: 8 GB DDR4
- GPU: NVIDIA GTX 1650 (4 GB)
- Library: OpenCV
- Test Duration: 60 seconds

### Test Configuration
- Camera Source: Built-in Laptop Webcam
- Resolution: 640x480
- Camera FPS: 30.00
- Image Processing: None
- Display: Enabled

### Results
| Trial | Test duration | Processed frames | Average FPS | Average CPU usage | Average RAM usage |
|---|---:|---:|---:|---:|---:|
| 1 | 60.34 s | 1789 | 29.65 | 23.07% | 109.81 MB |
| 2 | 60.35 s | 1788 | 29.63 | 14.30% | 105.98 MB |
| 3 | 60.36 s | 1790 | 29.65 | 21.42% | 104.26 MB |

### Observations
- The capture remained close to the camera's target rate.

### Conclusion
- OpenCV provided the higher throughput in this run and used substantially less RAM.

## Experiment 02: GStreamer Webcam Capture

### Environment
- CPU: Intel Core i5-10500H
- RAM: 8 GB DDR4
- GPU: NVIDIA GTX 1650 (4 GB)
- Library: GStreamer 1.28.8.1
- Test Duration: 60 seconds

### Test Configuration
- Camera Source: Built-in Laptop Webcam
- Resolution: 640x480
- Image Processing: None
- Display: Enabled through `fpsdisplaysink`

### Results
| Trial | Test duration | Processed frames | Average FPS | Average CPU usage | Average RAM usage |
|---|---:|---:|---:|---:|---:|
| 1 | 60.58 s | 1740 | 28.72 | 11.91% | 215.30 MB |
| 2 | 60.57 s | 1770 | 29.22 | 11.70% | 209.48 MB |
| 3 | 60.51 s | 1753 | 28.97 | 11.44% | 209.24 MB |

### Initial Trial Comparison with OpenCV

| Metric | OpenCV | GStreamer | Difference |
|---|---:|---:|---:|
| Average FPS | 29.65 | 28.72 | GStreamer -0.93 (-3.1%) |
| Average CPU usage | 23.07% | 11.91% | GStreamer -11.16 percentage points |
| Average RAM usage | 109.81 MB | 215.30 MB | GStreamer +105.49 MB |
| Total processed frames | 1789 | 1740 | GStreamer -49 (-2.7%) |

### Initial Trial Observations
- GStreamer reduced CPU usage by approximately 48% relative to OpenCV.
- GStreamer used approximately 96% more RAM in this configuration.
- Both pipelines maintained a frame rate close to the camera's target rate.

### Conclusion
- For this benchmark, GStreamer is preferable when lower CPU usage is the priority.
- OpenCV is preferable when lower memory usage and the highest measured throughput are more important.
- The implementation decision is to use GStreamer for the video-capture pipeline, because CPU efficiency is the primary requirement for the in-cabin monitoring workload.

## Overall Average (3 Trials per Technology)

| Metric | OpenCV average | GStreamer average | Difference |
|---|---:|---:|---:|
| Average FPS | 29.64 | 28.97 | GStreamer -0.67 (-2.3%) |
| Average CPU usage | 19.60% | 11.68% | GStreamer -7.92 percentage points |
| Average RAM usage | 106.68 MB | 211.34 MB | GStreamer +104.66 MB |
| Average processed frames per trial | 1789 | 1754 | GStreamer -35 (-2.0%) |

### Final Decision
- Across three trials, GStreamer used approximately 40% less CPU than OpenCV.
- OpenCV maintained approximately 2.3% higher average FPS and used approximately 50% less RAM.
- GStreamer remains the selected video-capture implementation because CPU efficiency is the primary requirement for the in-cabin monitoring workload.
