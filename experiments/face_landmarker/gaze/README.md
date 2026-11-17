# Geometric Eye Gaze Estimation

This experiment uses the existing 478 Face Landmarker landmarks without an
additional model.

For each eye it:

1. Averages the five iris landmarks to obtain the Iris Center.
2. Uses the eye corners as the horizontal axis.
3. Uses the upper- and lower-eyelid midpoints as the vertical axis.
4. Projects the Iris Center onto both axes.

The resulting `horizontal` and `vertical` values are normalized positions:

```text
0.0 -> first axis endpoint
1.0 -> second axis endpoint
```

The values are geometric measurements, not gaze classifications yet. Camera
perspective, eyelid occlusion, and person-specific eye geometry still require
calibration before defining `Left`, `Right`, `Up`, `Down`, or `Center`.

## Natural-gaze calibration

Run the calibration mode:

```bash
./.venv/Scripts/python.exe experiments/face_landmarker/gaze/calibrate.py
```

Keep the head still and look naturally at the camera. After a three-second
countdown, the script collects valid gaze measurements for ten seconds and
writes `calibration_results.md`.

For each eye, the report contains:

- Neutral horizontal and vertical references: the measured means.
- Horizontal and vertical ranges: the observed minimum and maximum values.
- Number of valid samples.

These are calibration measurements only. No gaze thresholds or direction
classifications are applied yet.

## Direction classification

The production classification module uses each eye's observed calibration range as its natural
gaze band:

- Inside `[min, max]`: `CENTER` for that axis.
- Below the horizontal range: `LEFT`.
- Above the horizontal range: `RIGHT`.
- Below the vertical range: `UP`.
- Above the vertical range: `DOWN`.

The deviation is normalized by the distance from Neutral to the exceeded range
boundary. Each eye is classified independently, then the combined result uses
the strongest non-center axis. The per-eye results and deviations are retained
in the output.

If an eye's horizontal semantic direction is reversed, pass
`horizontal_sign=-1` for that eye. The current corner ordering uses `+1` for
both eyes, but this remains configurable rather than assumed.

Run the live classifier with the saved calibration:

```bash
./.venv/Scripts/python.exe experiments/face_landmarker/gaze/monitor.py
```

The window displays the combined direction and the horizontal/vertical
classification for each eye. Press `Q` or `Esc` to exit.
