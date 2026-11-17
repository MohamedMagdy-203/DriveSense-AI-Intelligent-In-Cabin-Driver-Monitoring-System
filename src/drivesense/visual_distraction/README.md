# Visual Distraction

## Purpose

This package turns calibrated geometric gaze output into a camera-reference
assessment and tracks gaze events over time. It does not claim that the camera
reference represents every road-related gaze region.

## Components

- `gaze`: iris-center geometry, person-specific calibration, and direction
  classification.
- `assessment.py`: evaluates gaze relative to the camera reference and reports
  head-pose availability without head-direction thresholds.
- `glance_tracker.py`: opens and closes one `OFF_REFERENCE` event at a time.
- `glance_history.py`: stores completed events and returns overlapping ranges.
- `temporal.py`: evaluates active and completed glances using the prototype
  temporal criteria.

## Pipeline

```text
Gaze Classification
    -> Driving Gaze Assessment
    -> Glance Tracker
    -> Glance History
    -> Temporal Distraction Analyzer
```

`POTENTIAL_DISTRACTION` means that a temporal pattern crossed the current
prototype criteria. It is not proof of distraction. `UNAVAILABLE` means the
current assessment cannot be made and must not be interpreted as attention.

## Configuration and testing

Runtime values are loaded from
[`configs/default.yaml`](../../../configs/default.yaml). The criteria are
3-second long glance, 10 accumulated seconds within 30 seconds, and a
2-second re-engagement reset. They are design values inspired by protocol
examples, not universal thresholds.

Unit and integration tests use deterministic clocks and synthetic gaze/head
outputs. Run them with:

```bash
python -m pytest
```
