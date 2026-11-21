# DriveSense Final Release Record

## Scope

This document records the final prototype state and tested evidence. It does
not claim safety certification, Euro NCAP compliance, clinical validation, or
production-grade accuracy.

## Implemented system

DriveSense integrates:

- CPU MediaPipe Face Landmarker.
- GStreamer/OpenCV webcam capture.
- Gaze and head-pose supporting signals.
- PERCLOS and prolonged eye-closure prototype policy.
- Visual-distraction glance tracking and temporal analysis.
- Independent asynchronous YOLO phone detection.
- One typed `EngineFrameOutput` per processed frame.

## Verified evidence

| Evidence | Measured result |
|---|---|
| Full Python test suite | 45 passed |
| Short live webcam probe | 139 frames in approximately 5 seconds |
| Timed end-to-end smoke | 201 frames, 32.43 FPS, 0 camera read failures |
| 120-second stability run | 3561 frames, 32.27 FPS, 0 camera read failures |
| Stability peak RSS | 1563.19 MB |
| Stability final RSS | 482.36 MB |
| Stability average process CPU | 48.51% |
| Demo recording | 270 frames, 30 FPS container, 9 seconds |

Runtime measurements are from one Windows laptop webcam run and may vary
between machines and environments.

## Model and artifact setup

The runtime checkpoint is:

```text
artifacts/phone_detection/weights/best.pt
```

Weights are intentionally ignored by Git. Copy a verified artifact bundle to
the weight location, then run:

```powershell
python scripts/prepare_phone_artifacts.py C:\path\to\phone_detection_bundle
python scripts/prepare_phone_artifacts.py --verify-only
```

The tracked
[`model_manifest.json`](../artifacts/phone_detection/model_manifest.json)
stores SHA-256 values for the verified local weights.

## Scientific criteria

- Long gaze: 3 seconds.
- Cumulative gaze: 10 seconds within 30 seconds.
- PERCLOS: 60-second prototype rolling window.
- Prolonged closure test scenario: up to 4 seconds.
- Phone: detection only; no assumed phone-use time threshold.

The evidence and limitation details are in
[Driving Gaze and Distraction](05_driving_gaze_and_distraction.md).

## Demo

The existing live runtime can record an actual webcam session:

```powershell
python experiments/integration/live.py --duration 20 --record-output demo/drivesense_demo.mp4
```

The demo guide is in [demo/README.md](../demo/README.md).

## Known limitations

- No extensive multi-subject or multi-driver evaluation.
- Gaze calibration is person-specific and camera-reference-specific.
- PERCLOS and closure thresholds require additional validation.
- Phone detector generalization is limited to the prepared dataset.
- MediaPipe GPU acceleration was not available in the tested Windows build.
- Phone object detection does not establish phone use or distraction.
- The stability run is not a memory-leak proof.
- No alert system or safety decision was implemented.
