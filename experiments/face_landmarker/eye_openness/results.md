# Landmark-Based Eye Openness Calibration

This experiment uses the existing MediaPipe Face Landmarker only. Eye openness
is the average eyelid aperture divided by eye-corner width for both eyes. This
is a geometric openness proxy, not direct pupil-occlusion segmentation.

- Duration per state: `30 seconds`
- Valid open-eye frames: `878`
- Valid partial-closure frames: `883`
- Valid closed-eye frames: `883`

| State | Min | Max | Mean | Std Dev | 5th percentile | 95th percentile |
|---|---:|---:|---:|---:|---:|---:|
| Open Eyes | 0.0363 | 0.4347 | 0.3033 | 0.0747 | 0.1842 | 0.4140 |
| Partial Closure | 0.1400 | 0.4361 | 0.1928 | 0.0479 | 0.1539 | 0.2201 |
| Closed Eyes | 0.0399 | 0.3995 | 0.0816 | 0.0355 | 0.0510 | 0.1093 |

## Provisional calibrated mapping

For a future closure estimate, use the open and closed baselines rather than a
fixed EAR threshold:

```text
closure = clamp((open_baseline - current_openness)
                / (open_baseline - closed_baseline), 0, 1)
```

Using the collected means, the partial-closure estimate is
`49.9%` of the open-to-closed range. This is only a calibration
check; it is not direct measurement of 80% eyelid or pupil coverage.
