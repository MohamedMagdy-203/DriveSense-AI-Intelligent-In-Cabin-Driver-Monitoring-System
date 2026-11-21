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
ATTENTIVE / POTENTIAL_DISTRACTION
```

### 1. Driving Gaze Assessment

Determine whether the current eye-gaze estimate is inside the current
camera-referenced driving region. Use the calibrated geometric gaze output as
the primary input and retain Head Pose as a supporting signal.

### 2. Glance Event Tracking

Track each transition into and out of an off-reference gaze state. Each event currently retains:

- Start timestamp.
- End timestamp.
- Duration.

Gaze and head-pose details remain inputs to the assessment layer; enriching
events with those signals is future work.

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

## Drowsiness and phone reference criteria

The visual-distraction criteria above are prototype references:

- Long glance: `3 seconds`.
- Cumulative glance time: `10 seconds in 30 seconds`.
- Microsleep/prolonged-closure test scenario: continuous eye closure for up to
  `4 seconds`.

PERCLOS remains a separate temporal metric. Its window, closure score, and
blink-exclusion rule are configurable prototype inputs and are not a universal
drowsiness threshold. KSS 7 or 8 is retained as a human sleepiness reference
only; it is not directly converted to EAR or PERCLOS in this implementation.

The phone module reports detection only. A phone box is not converted into
phone use, distraction, or an alert because no universal time threshold is
defined for that behavior.

## Live webcam verification

Live webcam testing was performed with the integrated
`DriverMonitoringEngine` using `640x480` frames and the existing natural-gaze
calibration containing 299 valid gaze samples. A short probe processed 139
frames over approximately 5 seconds and returned `AVAILABLE` Face,
`ON_REFERENCE` Gaze, `ATTENTIVE` gaze assessment, `OPEN` Drowsiness, `0%`
PERCLOS, and `ATTENTIVE` Distraction.

This is one stationary live test result, not a general performance or
accuracy evaluation. It does not establish universal thresholds, clinical
drowsiness conclusions, or Euro NCAP/compliance behavior.

## References and evidence traceability

The following sources support the scientific concepts used in this prototype.
They do not establish that the implemented thresholds have been validated for
every driver, vehicle, lighting condition, or camera position.

1. Åkerstedt, T. and Gillberg, M. (1990), *Subjective and Objective Sleepiness
   in the Active Individual*. International Journal of Neuroscience, 52,
   29-37. DOI:
   [10.3109/00207459008994241](https://doi.org/10.3109/00207459008994241).
   Supports the subjective/objective sleepiness research context and KSS
   development; it does not define an EAR or PERCLOS threshold.
2. Kaida, K. et al. (2006), *Validation of the Karolinska sleepiness scale
   against performance and EEG variables*. Clinical Neurophysiology, 117,
   1574-1581. DOI:
   [10.1016/j.clinph.2006.03.011](https://doi.org/10.1016/j.clinph.2006.03.011).
   Supports KSS validation; it is not converted into webcam-derived thresholds
   by DriveSense.
3. Dinges, D.F. and Grace, R. (1998), *PERCLOS: A Valid Psychophysiological
   Measure of Alertness as Assessed by Psychomotor Vigilance Tasks*, Federal
   Highway Administration, FHWA-MCRT-98-006. Supports PERCLOS as a temporal
   eye-closure measure and shows that implementation definitions can vary.
4. European Parliament and Council (2019),
   [Regulation (EU) 2019/2144](https://eur-lex.europa.eu/eli/reg/2019/2144/oj),
   general safety and type-approval requirements. This is policy context for
   driver-monitoring research, not evidence that this prototype is compliant.
5. Euro NCAP,
   [Engineer Protocols](https://www.euroncap.com/en/for-engineers/protocols/).
   The 3-second and 4-second scenarios and phone-use scenarios are used only as
   engineering/test references. Exact protocol versions and their current
   definitions must be verified before making a compliance claim.

The 3-second long-glance, 10/30-second cumulative-glance, and 4-second
prolonged-closure values are project-specific prototype criteria. They are
configuration values informed by relevant practices, not universal thresholds
or scientifically proven danger limits.
