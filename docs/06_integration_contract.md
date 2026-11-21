# DriveSense Integration Contract

## Purpose

This document defines how the `DriverMonitoringEngine` invokes existing
modules and interprets their results. It separates signal collection,
classification, temporal analysis, and optional phone detection.

The contract does not define final alert thresholds or state that a phone
detection proves phone use by the driver.

## Module ownership

| Module | Input | Output |
|---|---|---|
| Face runtime | Webcam frame and increasing MediaPipe timestamp | Raw Face Landmarker result |
| Head pose | Face Landmarker result | `HeadPoseEstimate` |
| Head-pose temporal state | `HeadPoseEstimate` | `TemporalState` using the module's monotonic clock |
| Gaze geometry/classification | Face landmarks and calibration | `GazeClassification` |
| Visual-distraction assessment | Gaze and head-pose outputs | `DrivingGazeAssessment` |
| Glance tracker/history | Gaze assessment status | Active glance and completed events |
| Temporal distraction analyzer | History and active glance | `DistractionAssessment` |
| PERCLOS metrics | Timestamped eye-closure state | Closure percentage |
| Phone detector | Webcam frame | `PhoneObservation` |

## Runtime call order

Before the loop, initialize once:

1. Start GStreamer with `start_gstreamer()`.
2. Enter `create_landmarker()` as a context manager.
3. Create `HeadPoseEstimator`, `HeadPoseTemporalAnalyzer`, `PerclosWindow`,
   `GlanceTracker`, `GlanceHistory`, and `TemporalDistractionAnalyzer`.
4. Load gaze calibrations and make the gaze-classification implementation
   available to the engine.

For each captured frame:

1. Read a frame with `read_gstreamer_frame(...)`.
2. Produce a valid MediaPipe timestamp:
   `timestamp_ms = max(previous_timestamp_ms + 1, int(time.perf_counter() * 1000))`.
3. Convert and submit the frame with
   `landmarker.detect_for_video(face_image(frame), timestamp_ms)`.
4. If a face exists, derive EAR/openness and update PERCLOS with
   `perclos.update(timestamp_ms, closed_or_none)`. If no face exists, pass
   `None` to PERCLOS to reset its observation state.
5. Update `HeadPoseEstimator.update(result)`, then
   `HeadPoseTemporalAnalyzer.update(estimate)`.
6. Classify the gaze from calibrated iris positions.
7. Call `assess_driving_gaze(gaze_classification, head_pose)`.
8. Update `GlanceTracker.update(gaze_status)`. If it closes an event, add that
   `GlanceEvent` to `GlanceHistory`.
9. Call `TemporalDistractionAnalyzer.update(history, active_start_time,
   gaze_status)`.
10. Run optional phone detection independently and normalize its result.
11. Combine the frame outputs into `EngineFrameOutput`.

The Face runtime currently creates a MediaPipe `VIDEO` task and must keep its
own context manager open for the duration of the loop. It is not a live-stream
callback provider.

`DriverMonitoringEngine` owns this frame cycle. It can initialize the optional
`MediaPipeFaceProvider`, temporal state, PERCLOS, gaze/head posture, and phone
provider, then expose `update(frame, timestamp_ms) -> EngineFrameOutput`.
The face and phone providers are injected so hardware/model failures remain
explicit and the engine can be tested with synthetic providers.

`YOLOPhoneProvider` is the phone-provider adapter. It loads
`artifacts/phone_detection/weights/best.pt`, runs Ultralytics inference, filters
to phone class `0`, normalizes box coordinates to the frame dimensions, and
returns only `PhoneObservation`. Ultralytics objects, tensors, and results never
leave the adapter. Initialization failures are raised explicitly; per-frame
inference failures return `UNAVAILABLE` and set `last_error`.

## Phone result freshness

Asynchronous phone inference is throttled independently of face processing.
Each `PhoneObservation` carries:

- `timestamp_monotonic`: completion time for the latest inference.
- `freshness`: `FRESH`, `CACHED`, `STALE`, or `UNAVAILABLE`.

The async provider caches the latest valid result. A result becomes
`CACHED` while it is usable but no longer fresh, and `STALE` after twice the
submission interval (minimum 1 second). The runtime must not draw stale
detection boxes as current observations.

`UNAVAILABLE` means inference did not produce a usable observation. It is
distinct from `NOT_DETECTED`, which means inference completed and found no
phone box.

Provider lifecycle is explicit: enter/exit and `close()` release provider
resources. `AsyncYOLOPhoneProvider.close()` is idempotent, waits for executor
work to finish, and prevents new inference submissions after shutdown.

## Face observation contract

`MediaPipeFaceProvider.process_frame` converts MediaPipe's raw face collection
into `FaceObservation`. Engine-facing face output contains only:

- `status`: `AVAILABLE`, `NO_FACE`, or `UNAVAILABLE`;
- first-face landmarks;
- optional facial transformation matrix;
- MediaPipe frame timestamp.

A face is available only with at least 478 landmarks. Invalid or shorter
landmark data raises a provider conversion error and becomes `UNAVAILABLE`
rather than valid gaze or drowsiness input. The Engine never merges multiple
faces; it tracks the first face only.

`GlanceTracker.update` accepts `ON_REFERENCE`, `OFF_REFERENCE`, and
`UNAVAILABLE`, but not `UNDETERMINED`. `assess_gaze(None)` returns
`UNAVAILABLE`, so the engine should pass `UNAVAILABLE` for no usable gaze and
must not invent an `UNDETERMINED` glance state.

PERCLOS closure is an engine-policy input. The existing eye-closure experiment
uses `calibrated_closure_score(...)`, a closure threshold, and a 200 ms blink-
exclusion window before passing `closed=True` to `PerclosWindow.update`.
Those constants belong to drowsiness configuration; they are not part of
`PerclosWindow` itself.

The engine may process phone detection asynchronously or at a lower frame
rate. A missing phone result must be represented by `UNAVAILABLE`; it must not
be treated as `NOT_DETECTED`.

## Temporal clocks

- `GlanceTracker`, `GlanceHistory`, `TemporalDistractionAnalyzer`, and
  `HeadPoseTemporalAnalyzer` use module-owned `time.monotonic()` clocks.
  The engine must call `GlanceTracker.update` and
  `TemporalDistractionAnalyzer.update` in the sequence above because they
  generate or consume their own monotonic timestamps.
- MediaPipe `VIDEO` mode requires monotonically increasing timestamps in
  milliseconds. PERCLOS also expects an engine-provided millisecond timestamp.
- Phone inference time must not alter the MediaPipe, PERCLOS, glance, or
  head-pose timestamps.
- `FrameTimestamps` records both domains for `EngineFrameOutput`, but it does
  not replace the different APIs.

## Availability rules

| Condition | Contract result |
|---|---|
| One face and landmarks/matrix available | `AVAILABLE` |
| Result with no face | `NO_FACE` |
| Runtime exception or invalid frame | `UNAVAILABLE` |
| Phone box(es) | `DETECTED` |
| Completed phone inference with no boxes | `NOT_DETECTED` |
| Phone inference not run or failed | `UNAVAILABLE` |

An unavailable signal is separate from a negative signal:

- `NO_FACE` is not eye closure.
- `UNAVAILABLE` gaze is not attentive or off-reference.
- `UNAVAILABLE` phone status is not "no phone".
- Missing PERCLOS values remain `None`.

## Frame contract

The typed structures are in
[`src/drivesense/integration_contract.py`](../src/drivesense/integration_contract.py):

- `EngineFrameInput`: raw/categorized signals for one frame.
- `EngineFrameOutput`: normalized output for that frame.
- `PhoneObservation`: status plus optional normalized detections.
- `FaceSignalProvider` and `PhoneSignalProvider`: adapter protocols.

Phone coordinates and confidence use normalized or `[0, 1]` values.
The engine does not receive Ultralytics result objects directly.

## Failure behavior

The engine must fail explicitly for a camera or mandatory Face runtime error.
A missing face, missing matrix, or unavailable optional detector is a frame
state, not an exception that should silently alter the contract.

Exceptions from a provider may be logged and converted to
`UNAVAILABLE`, except for:

- camera-open/read failure;
- invalid configuration;
- invalid provider output shape or coordinates.

## Implementation status

`DriverMonitoringEngine.update(frame, timestamp_ms)` implements the frame call
order described above. It returns one `EngineFrameOutput` and does not implement
alert behavior. Existing module outputs and `UNAVAILABLE` states are preserved
until a signal is valid.

## Engineering responsibilities after refactoring

The Engine now coordinates providers and temporal modules but delegates:

- calibrated gaze processing to `GazeProcessor`;
- eye-openness/PERCLOS/prolonged-closure policy to `DrowsinessAnalyzer`;
- temporal distraction configuration to `TemporalDistractionAnalyzer`;
- phone lifecycle and inference conversion to phone providers.

This boundary keeps provider and feature-processing exceptions diagnosable
while preserving one `EngineFrameOutput` per frame.
