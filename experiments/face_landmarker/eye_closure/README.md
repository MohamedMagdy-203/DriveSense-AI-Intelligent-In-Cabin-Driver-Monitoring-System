# Eye closure monitor

Run the real-time monitor:

```bash
./.venv/Scripts/python.exe experiments/face_landmarker/eye_closure/monitor.py
```

The monitor uses per-frame EAR, a closed-eye threshold of `0.15`, and reports
`PROLONGED CLOSURE` after 500 milliseconds below the threshold.

It also displays session counters for:

- `Normal blinks`: a closed interval shorter than 500 milliseconds.
- `Prolonged closures`: a closed interval that reaches 500 milliseconds,
  counted once when the threshold is crossed.

Each completed closure is appended to `events.csv` with:

`timestamp`, `event_type`, `duration_ms`, `right_ear`, and `left_ear`.

When the window is closed with `Q` or `Esc`, the terminal prints the session
totals, average blink duration, and longest eye closure.

The monitor also displays `PERCLOS (60s)`, calculated from timestamped
durations in a rolling 60-second window. PERCLOS uses the calibrated
landmark-based `closure_score`:

```text
closure_score = clamp(
    (open_baseline - current_openness)
    / (open_baseline - closed_baseline),
    0,
    1,
)
```

Only scores of `0.8` or higher contribute closed time. Closures lasting
`200 ms` or less are excluded as operationally defined normal blinks. The
`0.8` threshold is a geometric calibration threshold, not proof of 80% pupil
or eyelid coverage.
