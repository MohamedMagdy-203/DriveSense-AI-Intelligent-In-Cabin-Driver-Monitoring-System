# Drowsiness Metrics

`drivesense.drowsiness.metrics` contains reusable timestamp-based metrics
extracted from the eye-closure experiment.

- `PerclosWindow` calculates a rolling PERCLOS percentage from observed
  closed/open segments.
- `calibrated_closure_score` maps calibrated openness baselines to a clamped
  closure score.

The eye-closure monitor remains under
`experiments/face_landmarker/eye_closure/` because camera display, CSV logging,
and session reporting are experiment-specific. It imports these production
metrics instead of maintaining a duplicate implementation.
