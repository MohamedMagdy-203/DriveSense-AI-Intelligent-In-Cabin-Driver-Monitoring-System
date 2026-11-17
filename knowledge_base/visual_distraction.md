# Visual Distraction Detection

## Purpose

The visual-distraction subsystem estimates whether the driver's gaze is
directed toward a temporary camera-centered reference and analyzes the timing
of glances away from it. It is a research prototype, not a regulatory
compliance implementation.

## Current architecture

```text
MediaPipe Face Landmarker
    -> Iris Geometry and Calibration
    -> Gaze Classification
    -> Driving Gaze Assessment
    -> Glance Tracker
    -> Glance History
    -> Temporal Distraction Analyzer
```

The production implementation is under
[`src/drivesense/visual_distraction/`](../src/drivesense/visual_distraction/).

## Implemented behavior

### Gaze

The system calculates normalized iris positions using five iris landmarks per
eye, supports separate per-eye calibration, and classifies:

- `CENTER`
- `LEFT`
- `RIGHT`
- `UP`
- `DOWN`

`CENTER` maps to `ON_REFERENCE`; other classified directions map to
`OFF_REFERENCE`. Missing or invalid gaze data maps to `UNAVAILABLE`.

### Head pose

Head pose is a supporting availability signal. The relative rotation is
calculated using the neutral reference:

```text
R_relative = R_neutral.T @ R_current
```

The latest controlled recording captured `410` matrices:

| Pose | Matrices |
|---|---:|
| Neutral | 89 |
| Turn Left | 85 |
| Turn Right | 58 |
| Look Up | 89 |
| Look Down | 89 |

The observed sign conventions were preserved as follows:

- Turn Left: `Z negative` in `98.82%` of frames.
- Turn Right: `Z positive` in `100%` of frames.
- Look Up: `X negative` in `100%` of frames.
- Look Down: `X positive` in `100%` of frames.

These are diagnostic results from one controlled recording and are not
universal pose thresholds.

## Assessment semantics

`ATTENTIVE` is currently limited to gaze being on the camera reference while
a valid head-pose estimate is available. Off-reference gaze remains
`UNDETERMINED` until temporal analysis evaluates its duration and repetition.
The system does not independently label every head movement as distraction.

## Limitations

- The camera-centered reference is only a temporary proxy for a driving region.
- `POTENTIAL_DISTRACTION` is not proof of distraction.
- `UNAVAILABLE` means that assessment is not currently possible; it does not
  mean the driver is attentive.
- Results need validation across users, camera mounting positions, lighting,
  seating positions, and tracking-loss conditions.
- Phone-usage detection and final alert decisions are not implemented.