# EAR calibration

Run the frame-level open-eyes calibration, which records EAR for every valid
face frame:

```bash
./.venv/Scripts/python.exe experiments/face_landmarker/ear_calibration/calibrate.py --open-frame
```

The report is written to `open_frame_results.md`. The default mode records one
sample per second and writes `results.md`; the existing `results.md` contains
the earlier two-condition open/closed calibration run.
