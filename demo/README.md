# DriveSense Demo Recording

Use the existing end-to-end monitoring window to record a short portfolio
demonstration. The recording is actual webcam output, not a synthetic dashboard
or staged UI.

## Recommended 20-second recording

```powershell
python scripts/prepare_phone_artifacts.py --verify-only
python experiments/integration/live.py --duration 20 --record-output demo/drivesense_demo.mp4
```

A valid trained `best.pt` checkpoint must exist at
`artifacts/phone_detection/weights/best.pt`.

## Suggested sequence

1. Start with face visible and natural gaze.
2. Show normal open-eye drowsiness and PERCLOS.
3. Turn gaze away for at least 3 seconds to demonstrate visual distraction.
4. Return to the camera reference.
5. Show a phone object if available and safe.
6. Temporarily remove the face to demonstrate `NO_FACE`.
7. End the recording naturally; do not manufacture errors or false states.

Record only if you have consent and camera permissions. Do not include personal
data beyond what is needed for the demo.

## Captured material

The runtime draws:

- Face status.
- Gaze status.
- Drowsiness status.
- PERCLOS.
- Distraction status.
- Phone detection status and freshness.
- FPS, frame latency, and process RSS.

This demo demonstrates software behavior under a single local webcam session.
It is not a multi-driver evaluation, clinical drowsiness test, or Euro NCAP
validation.

## Recorded evidence placeholder

No demonstration video is currently committed to this repository.
After recording a suitable consented demo, place or link the final video here
and update the main README Demo section.
