# Head Pose

## Purpose

This package estimates a relative rotation vector from MediaPipe facial
transformation matrices and stores a short history of valid estimates.

## Components

- `HeadPoseEstimator`: removes uniform scale, calibrates the first valid
  matrix as Neutral, and returns X/Y/Z degrees plus magnitude.
- `HeadPoseTemporalAnalyzer`: timestamps valid estimates with
  `time.monotonic()` and retains the configured two-second window.

Missing faces and matrices remain explicit `NO_FACE` and `NO_MATRIX` states and
are not added to the valid rotation history.

## Design boundary

The package does not assign `ON_REFERENCE` or `OFF_REFERENCE` to head pose.
Driving-reference thresholds remain a later design decision.

## Testing

Synthetic rotation and temporal-history cases are covered by
`tests/unit/test_head_pose.py`. Matrix collection and axis validation remain
under `experiments/head_pose/`.
