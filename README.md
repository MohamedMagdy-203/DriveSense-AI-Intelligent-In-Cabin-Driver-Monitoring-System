# DriveSense AI

## Project Overview

DriveSense AI is an intelligent in-cabin Driver Monitoring System (DMS) that uses computer vision to detect driver fatigue, visual distraction, and potential mobile phone usage in real time. The system is designed to improve driver awareness and road safety through timely visual and audio alerts.

The initial development target is a PC or laptop with an RGB webcam and local processing. The architecture is intended to remain modular and hardware-independent so that it can later be adapted for edge AI devices.

## Work Completed

### Project Structure

- Added the initial Python project structure under `src/drivesense/`.
- Organized reproducible computer-vision experiments under `experiments/`.
- Added shared CPU-only MediaPipe Face Landmarker and GStreamer runtime helpers.
- Added landmark inspection, EAR calibration, eye-openness calibration, and eye-closure monitoring experiments.
- Added separate OpenCV, GStreamer, and MediaPipe pipeline benchmarks with stored results.
- Added `.gitignore`, `.env.example`, and `requirements.txt`.

### Documentation

- Added the problem definition document.
- Added functional and non-functional system requirements.
- Added the development hardware baseline.
- Documented the CPU-only MediaPipe constraint and benchmark findings.
- Documented the calibrated landmark-based eye-openness and PERCLOS approach.
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
│   ├── 02_requirements.md
│   ├── 03_system_architecture.md
│   └── 04_model_selection.md
├── experiments/
│   ├── face_landmarker/
│   │   ├── benchmark/
│   │   ├── common/
│   │   ├── ear_calibration/
│   │   ├── eye_closure/
│   │   ├── eye_openness/
│   │   └── landmark_inspection/
│   └── video_processing/
│       ├── gstreamer/
│       ├── mediapipe_pipeline/
│       ├── opencv/
│       └── summary/
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
- [System architecture](docs/03_system_architecture.md): current pipeline structure and component responsibilities.
- [Model selection](docs/04_model_selection.md): MediaPipe CPU decision and benchmark constraints.

## Running the Experiments

The commands below assume the repository root and the Windows virtual
environment used by the project:

```bash
./.venv/Scripts/python.exe experiments/face_landmarker/landmark_inspection/inspect.py
./.venv/Scripts/python.exe experiments/face_landmarker/ear_calibration/calibrate.py
./.venv/Scripts/python.exe experiments/face_landmarker/eye_openness/calibrate.py
./.venv/Scripts/python.exe experiments/face_landmarker/eye_closure/monitor.py
```

The eye-closure monitor uses GStreamer for camera capture, CPU MediaPipe for
landmarks, and OpenCV for conversion and display. Press `Q` or `Esc` to stop
the live monitor.

## Current Status

The MediaPipe Face Landmarker prototype is implemented and benchmarked on the
CPU. GStreamer is the selected camera pipeline, with OpenCV used for frame
conversion and display. The eye-closure monitor currently provides:

- Per-frame right-eye, left-eye, and average EAR.
- `OPEN`, `CLOSED`, and `PROLONGED CLOSURE` states.
- Normal blink and prolonged-closure counters.
- CSV event logging in `experiments/face_landmarker/eye_closure/events.csv`.
- A 60-second, timestamp-based PERCLOS sliding window.
- A calibrated landmark-based `closure_score` threshold of `0.8`.

The closure score is a geometric calibration proxy, not direct measurement of
80% eyelid or pupil coverage. Application-level temporal decision logic,
alerting, and production integration remain future work.

## Experiments

| Directory | Purpose |
|---|---|
| `experiments/face_landmarker/common/` | Shared MediaPipe, GStreamer, and EAR helpers. |
| `experiments/face_landmarker/landmark_inspection/` | Inspect the 478 landmarks and visualize eye indices. |
| `experiments/face_landmarker/ear_calibration/` | Calibrate EAR and save frame-level statistics. |
| `experiments/face_landmarker/eye_closure/` | Monitor eye states, blink events, calibrated closure score, and PERCLOS. |
| `experiments/face_landmarker/eye_openness/` | Calibrate open, partial, and closed eye geometric baselines. |
| `experiments/face_landmarker/benchmark/` | CPU Face Landmarker benchmark and results. |
| `experiments/video_processing/` | OpenCV, GStreamer, and MediaPipe pipeline benchmarks. |
| `experiments/video_processing/summary/` | Aggregate video-processing benchmark results. |

## Planned Next Steps

1. Validate the calibrated closure score across additional users and lighting conditions.
2. Evaluate whether the geometric proxy is sufficient for the required PERCLOS use case.
3. Implement the Temporal Decision Engine for combined fatigue signals.
4. Add configurable visual and audio alerts.
5. Add head-pose, visual-distraction, and mobile-phone analysis.
6. Add focused unit and integration tests.
7. Integrate the validated prototype into `src/drivesense/`.
