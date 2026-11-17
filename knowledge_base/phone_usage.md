# Phone Usage Detection

## Current status

Phone-usage detection is intentionally **not implemented** in the current
prototype. This knowledge-base entry records the scope boundary so that
future work does not get confused with the implemented gaze, head-pose, or
drowsiness components.

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