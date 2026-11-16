# Eye Openness Calibration

This experiment evaluates whether existing Face Landmarker eye points can
provide a calibrated eye-openness proxy without adding another model.

Run it from the repository root:

```bash
./.venv/Scripts/python.exe experiments/face_landmarker/eye_openness/calibrate.py
```

Keep the eyes naturally open during the first 30-second phase, half-close both
eyes during the second phase, and close both eyes during the third phase. The
report is written to `results.md`.
