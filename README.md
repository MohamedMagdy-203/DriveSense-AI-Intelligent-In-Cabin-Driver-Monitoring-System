# DriveSense AI

## Project Overview

DriveSense AI is an intelligent in-cabin Driver Monitoring System (DMS) that uses computer vision to detect driver fatigue, visual distraction, and potential mobile phone usage in real time. The system is designed to improve driver awareness and road safety through timely visual and audio alerts.

The initial development target is a PC or laptop with an RGB webcam and local processing. The architecture is intended to remain modular and hardware-independent so that it can later be adapted for edge AI devices.

## Work Completed

### Project Structure

- Created the initial Python project structure under `src/drivesense/`.
- Added placeholder modules for camera input, detection, fatigue analysis, distraction analysis, alerts, configuration, and the application entry point.
- Added the initial test package and test placeholders.
- Added folders for raw data, processed data, models, configuration, scripts, notebooks, and logs.
- Added `.gitignore`, `.env.example`, and `requirements.txt`.

### Documentation

- Added the problem definition document.
- Added functional and non-functional system requirements.
- Added the development hardware baseline.
- Added a knowledge-base directory for research and technical references covering:
  - Drowsiness detection
  - Mobile phone usage
  - Temporal decision engines
  - Visual distraction

## Project Structure

```text
DriveSense-AI-Intelligent-In-Cabin-Driver-Monitoring-System/
├── src/
│   └── drivesense/
│       ├── __init__.py
│       ├── main.py
│       ├── camera.py
│       ├── detection.py
│       ├── fatigue.py
│       ├── distraction.py
│       ├── alerts.py
│       └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_camera.py
│   ├── test_detection.py
│   ├── test_fatigue.py
│   └── test_distraction.py
├── docs/
│   ├── 01_problem_definition.md
│   └── 02_requirements.md
├── knowledge_base/
│   ├── drowsiness_detection.md
│   ├── phone_usage.md
│   ├── temporal_decision_engine.md
│   └── visual_distraction.md
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── config/
├── scripts/
├── notebooks/
├── logs/
├── requirements.txt
├── .env.example
└── .gitignore
```

## File and Directory Descriptions

### Root Files

| Path | Description |
|---|---|
| `README.md` | Main project overview, current progress, requirements summary, structure, limitations, and planned work. |
| `requirements.txt` | List of Python dependencies required by the project. It is currently a placeholder. |
| `.env.example` | Template for environment variables and local configuration values. |
| `.gitignore` | Specifies generated files, environments, logs, model files, and local data that Git should ignore. |

### Source Code: `src/drivesense/`

| Path | Description |
|---|---|
| `src/` | Main source-code directory. |
| `src/drivesense/` | Python package containing the DriveSense application code. |
| `src/drivesense/__init__.py` | Marks `drivesense` as a Python package. |
| `src/drivesense/main.py` | Intended application entry point for starting the monitoring system. |
| `src/drivesense/camera.py` | Intended camera-input module for capturing frames from an RGB webcam. |
| `src/drivesense/detection.py` | Intended shared detection module for face, eyes, head pose, and other visual features. |
| `src/drivesense/fatigue.py` | Intended fatigue and drowsiness analysis module. |
| `src/drivesense/distraction.py` | Intended visual-distraction and mobile-phone-usage analysis module. |
| `src/drivesense/alerts.py` | Intended module for visual and audio driver warnings. |
| `src/drivesense/config.py` | Intended module for application settings, thresholds, input configuration, and hardware options. |

### Tests: `tests/`

| Path | Description |
|---|---|
| `tests/` | Test suite directory for validating project components. |
| `tests/__init__.py` | Marks the test directory as a Python package. |
| `tests/test_camera.py` | Reserved for camera-capture tests. |
| `tests/test_detection.py` | Reserved for face and visual-detection tests. |
| `tests/test_fatigue.py` | Reserved for fatigue and drowsiness-analysis tests. |
| `tests/test_distraction.py` | Reserved for distraction and phone-usage tests. |

### Documentation: `docs/`

| Path | Description |
|---|---|
| `docs/` | Project documentation directory. |
| `docs/01_problem_definition.md` | Defines the driver-monitoring problem, project purpose, advantages, scope, limitations, and expected outcome. |
| `docs/02_requirements.md` | Defines operational context, functional requirements, non-functional requirements, hardware baseline, constraints, metrics, and scope limitations. |

### Research Knowledge Base: `knowledge_base/`

| Path | Description |
|---|---|
| `knowledge_base/` | Research and technical-reference directory used to guide system design. |
| `knowledge_base/drowsiness_detection.md` | Reserved for research and design information about drowsiness detection. |
| `knowledge_base/phone_usage.md` | Reserved for research and design information about detecting mobile-phone usage. |
| `knowledge_base/temporal_decision_engine.md` | Reserved for research and design information about combining detections over time. |
| `knowledge_base/visual_distraction.md` | Reserved for research and design information about visual distraction detection. |

### Data and Runtime Directories

| Path | Description |
|---|---|
| `data/` | Directory for datasets and image/video data used by the project. |
| `data/raw/` | Stores original, unprocessed input data. |
| `data/raw/.gitkeep` | Keeps the empty raw-data directory tracked by Git. |
| `data/processed/` | Stores cleaned, transformed, or prepared data. |
| `data/processed/.gitkeep` | Keeps the empty processed-data directory tracked by Git. |
| `models/` | Stores trained or downloaded computer-vision model files. |
| `models/.gitkeep` | Keeps the empty models directory tracked by Git. |
| `logs/` | Stores application logs and detection-event logs during development or execution. |
| `logs/.gitkeep` | Keeps the empty logs directory tracked by Git. |

### Supporting Directories

| Path | Description |
|---|---|
| `config/` | Stores external configuration files for thresholds, camera settings, and runtime options. |
| `config/.gitkeep` | Keeps the empty configuration directory tracked by Git. |
| `scripts/` | Stores utility scripts for data preparation, training, benchmarking, and project automation. |
| `scripts/.gitkeep` | Keeps the empty scripts directory tracked by Git. |
| `notebooks/` | Stores exploratory data-analysis, experimentation, and model-development notebooks. |
| `notebooks/.gitkeep` | Keeps the empty notebooks directory tracked by Git. |

## Project Documentation

Detailed project information is maintained in the documentation files:

- [Problem definition](docs/01_problem_definition.md): problem statement, purpose, advantages, project scope, limitations, and expected outcome.
- [System requirements](docs/02_requirements.md): operational context, functional requirements, non-functional requirements, hardware baseline, engineering constraints, evaluation metrics, and scope limitations.

## Current Status

The MediaPipe Face Landmarker prototype is implemented and benchmarked on the
CPU. GStreamer is the selected camera pipeline, with OpenCV used for frame
conversion and display. EAR calibration and real-time eye-closure monitoring
are available under `experiments/face_landmarker/`. The application-level
temporal decision engine, alerting behavior, event logging, and production
integration remain future work.

## Experiments

| Directory | Purpose |
|---|---|
| `experiments/face_landmarker/common/` | Shared MediaPipe, GStreamer, and EAR helpers. |
| `experiments/face_landmarker/landmark_inspection/` | Inspect the 478 landmarks and visualize eye indices. |
| `experiments/face_landmarker/ear_calibration/` | Calibrate EAR and save frame-level statistics. |
| `experiments/face_landmarker/eye_closure/` | Monitor `OPEN`, `CLOSED`, and `PROLONGED CLOSURE` states. |
| `experiments/face_landmarker/benchmark/` | CPU Face Landmarker benchmark and results. |
| `experiments/video_processing/` | OpenCV, GStreamer, and MediaPipe pipeline benchmarks. |
| `experiments/video_processing/summary/` | Aggregate video-processing benchmark results. |

## Planned Next Steps

1. Select and configure the computer vision dependencies.
2. Implement configurable RGB camera capture.
3. Implement face, eye, and head-pose detection.
4. Add drowsiness and visual-distraction analysis.
5. Add mobile phone detection and interaction analysis.
6. Implement the Temporal Decision Engine.
7. Add visual and audio alerts.
8. Add event logging and timestamp recording.
9. Benchmark FPS, latency, resource usage, and detection performance.
10. Add unit and integration tests.
