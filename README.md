# DriveSense AI

DriveSense AI is a CPU-first in-cabin Driver Monitoring System prototype. It
uses MediaPipe Face Landmarker, GStreamer, and OpenCV to investigate fatigue,
visual distraction, and future driver-monitoring capabilities.

The repository separates reusable production modules from calibration,
benchmark, data-collection, and live-demo experiments. The current work does
not claim regulatory compliance or production distraction classification.

## Architecture

```text
Camera / GStreamer
    -> Face Runtime
    -> Gaze + Head Pose
    -> Driving Gaze Assessment
    -> Glance Tracker
    -> Glance History
    -> Temporal Distraction Analyzer
```

Reusable code is under `src/drivesense/`. Experiment scripts under
`experiments/` import those modules and preserve the project's research and
calibration history.

## Project structure

```text
.
├── configs/
│   ├── default.yaml
│   └── README.md
├── docs/
├── experiments/
│   ├── face_landmarker/
│   ├── head_pose/
│   └── video_processing/
├── knowledge_base/
├── models/
├── src/
│   └── drivesense/
│       ├── config.py
│       ├── face/
│       ├── head_pose/
│       └── visual_distraction/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── README.md
├── pyproject.toml
└── requirements.txt
```

## Production modules

| Module | Responsibility |
|---|---|
| `drivesense.config` | Load and validate YAML settings. |
| `drivesense.face.runtime` | CPU MediaPipe Face Landmarker and GStreamer helpers. |
| `drivesense.head_pose` | Relative rotation-vector estimation and valid history. |
| `drivesense.visual_distraction.gaze` | Iris geometry, calibration, and classification. |
| `drivesense.visual_distraction` | Assessment, glance events, history, and temporal analysis. |

Module-specific design and test details are documented in:

- [Face runtime](src/drivesense/face/README.md)
- [Head pose](src/drivesense/head_pose/README.md)
- [Visual distraction](src/drivesense/visual_distraction/README.md)
- [Configuration](configs/README.md)
- [Tests](tests/README.md)

## Configuration

Runtime settings are in [configs/default.yaml](configs/default.yaml). The
current configuration preserves the existing behavior:

- CPU MediaPipe delegate.
- Camera index `0`, resolution `640x480`.
- Face detection, presence, and tracking confidence `0.5`.
- Head-pose history window `2` seconds.
- Prototype glance criteria: `3` seconds, `10` seconds within `30` seconds,
  and `2` seconds re-engagement.

The temporal values are engineering criteria inspired by protocol examples,
not universal thresholds and not proof of driver distraction.

## Installation and tests

```powershell
./.venv/Scripts/python.exe -m pip install -e ".[test]"
./.venv/Scripts/python.exe -m pytest
```

The ordinary test suite uses synthetic inputs and deterministic clocks; it
does not require a physical camera.

## Running experiments

From the repository root:

```powershell
./.venv/Scripts/python.exe experiments/face_landmarker/landmark_inspection/inspect.py
./.venv/Scripts/python.exe experiments/face_landmarker/ear_calibration/calibrate.py
./.venv/Scripts/python.exe experiments/face_landmarker/eye_openness/calibrate.py
./.venv/Scripts/python.exe experiments/face_landmarker/eye_closure/monitor.py
./.venv/Scripts/python.exe experiments/face_landmarker/gaze/calibrate.py
./.venv/Scripts/python.exe experiments/face_landmarker/gaze/monitor.py
./.venv/Scripts/python.exe experiments/head_pose/monitor.py
```

Live scripts require a compatible webcam and GStreamer installation. Press
`Q` or `Esc` to stop display-based monitors.

## Documentation

- [Problem definition](docs/01_problem_definition.md)
- [Requirements](docs/02_requirements.md)
- [System architecture](docs/03_system_architecture.md)
- [Model selection](docs/04_model_selection.md)
- [Driving gaze and distraction](docs/05_driving_gaze_and_distraction.md)
- [Experiments](experiments/README.md)

## Current limitations

- The camera-centered gaze reference is not a complete driving-region model.
- `POTENTIAL_DISTRACTION` is a preliminary temporal result.
- `UNAVAILABLE` means that an assessment is not currently possible; it does
  not mean the driver is attentive.
- Head pose is currently an availability/supporting signal, not an independent
  distraction criterion.
- The MediaPipe Windows runtime is CPU-only in the tested environment.
- Phone-usage detection and final alert decisions are not implemented.
