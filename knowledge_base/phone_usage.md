# Phone Usage Detection

## Current status

Phone **object detection** is implemented as a prepared dataset and a trained
YOLO11n prototype.

Phone **usage behavior classification** is not implemented. The current model
detects a phone object in an image; it does not decide that a driver is using
it, holding it, or operating it. It must not be confused with gaze, head-pose,
or drowsiness behavior analysis.

## Planned responsibility

A future phone-usage component may combine camera evidence such as hand,
object, and driver-interaction cues. It must expose an explicit unavailable or
undetermined state when the required evidence is missing.

It must not infer phone usage solely from:

- An off-reference gaze.
- A head movement.
- An eye-closure event.
- A missing face or landmark frame.

## Integration boundary

Phone usage should be added as an independent signal rather than embedded in
the visual-distraction temporal analyzer. Any future implementation should
have its own configuration, tests, validation data, and documented error
states before it is connected to alert decisions.