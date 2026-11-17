# Driving Gaze and Distraction Design Reference

## Purpose

This document records the design decisions adopted for the first
Driving-Gaze and distraction-analysis phase of DriveSense AI. It is an
engineering reference, not a claim that the prototype is compliant with any
regulation.

## Evidence-informed principles

The system should not classify a driver as distracted merely because head pose
and eye gaze are not both centered. Real driver-monitoring systems consider:

- Whether the visual attention is directed toward a driving-related region.
- The duration of each glance away from that region.
- Repeated short glances and their accumulated duration.
- Context and the type of visual behavior.

Eye Gaze is the primary signal for visual-attention assessment. Head Pose is a
supporting signal that can reinforce a gaze observation or help when gaze is
temporarily unreliable.

The cited protocols and research provide evaluation concepts and examples;
their timing values are not automatically universal thresholds for this
prototype.

## Adopted prototype decisions

### Driving reference

For the current prototype, the physical camera position is treated as the
forward driving direction. Therefore, the calibrated camera-centered gaze
reference is temporarily used as the effective `ON_ROAD` reference.

This is an explicit prototype assumption. It must be revisited if the camera
position, mounting angle, seat position, or vehicle geometry changes.

`CENTER` currently means centered relative to the camera calibration. It does
not claim to represent every real-world road region or all driver-attention
requirements.

### Signal roles

```text
Eye Gaze  -> primary visual-attention signal
Head Pose -> supporting signal
```

Head Pose must not independently convert every non-neutral movement into
`DISTRACTED`. A disagreement between eye gaze and head pose is a valid
behavioral state and should be retained for later temporal reasoning.

## Planned processing pipeline

```text
Head Pose + Eye Gaze
        |
        v
Driving Gaze Assessment
        |
        v
Glance Event Tracking
        |
        v
Temporal Distraction Analysis
        |
        v
ATTENTIVE / DISTRACTED
```

### 1. Driving Gaze Assessment

Determine whether the current eye-gaze estimate is inside the current
camera-referenced driving region. Use the calibrated geometric gaze output as
the primary input and retain Head Pose as a supporting signal.

### 2. Glance Event Tracking

Track each transition into and out of an off-reference gaze state. Each event
should retain at least:

- Start timestamp.
- End timestamp.
- Duration.
- Gaze direction and per-eye classification.
- Head Pose rotation vector and availability status.
- Whether the face or transformation matrix was temporarily unavailable.

### 3. Temporal Distraction Analysis

Evaluate sustained glances, repeated short glances, and accumulated
off-reference time. Timing values must be explicitly labeled as prototype
configuration until they are validated against the intended use case.

The current prototype configuration uses the following design values:

- Long glance: `>= 3` seconds.
- Repeated short glances: `>= 10` accumulated seconds within `30` seconds.
- Re-engagement reset: `>= 2` continuous seconds on the reference.

These values are design criteria inspired by examples from Euro NCAP and
related driver-monitoring research. They are not universal thresholds and do
not by themselves prove that a driver is distracted. `POTENTIAL_DISTRACTION`
is therefore the current temporal result; a production decision requires
validated driving regions, context, and further evaluation.

`UNAVAILABLE` means that the current assessment cannot be made. It must not be
interpreted as evidence that the driver is attentive.

## Current implementation boundary

The prototype currently provides:

- Geometric Iris Center and normalized eye coordinates.
- Per-eye natural-gaze calibration.
- `CENTER`, `LEFT`, `RIGHT`, `UP`, and `DOWN` gaze classifications.
- Relative Head Pose Rotation Vector X/Y/Z values.
- A short valid Head Pose history with explicit missing-data states.
- Glance tracking, complete glance history, and preliminary temporal analysis.

The following are not yet implemented in this phase:

- A production driving-region model.
- Regulatory compliance claims.
- A new trained gaze or driver-monitoring model.

## Validation requirements

Before treating the camera-centered reference as a robust driving reference,
evaluate changes in:

- Camera mounting position and angle.
- Driver seating position.
- Lighting.
- Different users and eye geometries.
- Temporary face or iris tracking loss.
- Eye-gaze and Head-Pose disagreement.
