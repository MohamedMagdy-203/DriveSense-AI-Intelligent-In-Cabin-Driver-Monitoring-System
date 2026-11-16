# Head Pose Experiments

These experiments use the existing CPU MediaPipe Face Landmarker. The shared
configuration enables `output_facial_transformation_matrixes=True`; no
additional model is used.

## Current module

[`head_pose.py`](./head_pose.py) provides `HeadPoseEstimator`:

- Removes the uniform scale from each `4x4` facial transformation matrix.
- Uses the first valid matrix as the Neutral reference.
- Computes `R_neutral.T @ R_current`.
- Returns a relative Rotation Vector with `x_deg`, `y_deg`, `z_deg`, and
  `magnitude_deg`.
- Reports `OK`, `NO_FACE`, and `NO_MATRIX` explicitly.

[`temporal.py`](./temporal.py) provides `HeadPoseTemporalAnalyzer`:

- Adds `time.monotonic()` timestamps.
- Retains valid samples from the latest 2-second window.
- Keeps the current `NO_FACE` or `NO_MATRIX` state without adding it to the
  rotation history.
- Does not apply smoothing or movement thresholds yet.

Run the live module demo:

```bash
./.venv/Scripts/python.exe experiments/head_pose/monitor.py
```

The first valid face matrix becomes Neutral. The window displays the current
status, Rotation Vector, magnitude, and valid sample count. Press `Q` or `Esc`
to exit.

## Matrix inspection

Inspect one returned transformation matrix:

```bash
./.venv/Scripts/python.exe experiments/head_pose/inspect_matrix.py
```

The 10-second inspection records the matrix count, shape, and first matrix
values in `results.md`.

## Per-frame recording

Record every available matrix for five controlled poses:

```bash
./.venv/Scripts/python.exe experiments/head_pose/record_motion_frames.py
```

The experiment records three seconds of each pose after an eight-second
preparation countdown:

1. Neutral
2. Turn Left
3. Turn Right
4. Look Up
5. Look Down

Outputs:

- `motion_frames.csv`: one `4x4` matrix per detected face and frame.
- `motion_results.md`: recorded-frame counts by pose.

## Frame-based validation

Analyze the recorded matrices without starting the camera:

```bash
./.venv/Scripts/python.exe experiments/head_pose/validate_axes.py
```

The analyzer:

- Removes scale and computes a relative Rotation Vector for every frame.
- Reports Median, P10, and P90 for X/Y/Z for each pose.
- Reports the percentage of frames preserving the expected sign.
- Writes per-frame vectors to `motion_rotation_vectors.csv`.
- Writes the summary to `axis_validation_results.md`.

The current empirical convention is diagnostic only:

```text
Turn Left  -> Z negative
Turn Right -> Z positive
Look Up    -> X negative
Look Down  -> X positive
```

No final Yaw/Pitch/Roll labels or smoothing thresholds have been introduced.
