# Face Runtime

## Purpose

`drivesense.face.runtime` owns the shared CPU MediaPipe Face Landmarker and
GStreamer runtime used by live experiments.

## Responsibilities

- Load the configured Face Landmarker model with the CPU delegate.
- Capture `640x480` frames through the configured GStreamer pipeline.
- Convert frames to MediaPipe images.
- Provide shared landmark, EAR, and eye-openness helpers.

The runtime does not make drowsiness or distraction decisions.

## Configuration

Settings are loaded from [`configs/default.yaml`](../../../configs/default.yaml)
through `drivesense.config`. The model path, camera index, resolution, window
name, and MediaPipe confidence values are validated before use.

## Testing

Mathematical helpers are covered by unit tests. Camera and live MediaPipe
execution require hardware and are kept outside ordinary unit tests.
