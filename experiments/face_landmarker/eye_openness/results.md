# Landmark-Based Eye Openness Calibration

This experiment uses the existing MediaPipe Face Landmarker only. Eye openness
is the average eyelid aperture divided by eye-corner width for both eyes. This
is a geometric openness proxy, not direct pupil-occlusion segmentation.

- Duration per state: `30 seconds`
- Valid open-eye frames: `883`
- Valid partial-closure frames: `884`
- Valid closed-eye frames: `884`

| State | Min | Max | Mean | Std Dev | 5th percentile | 95th percentile |
|---|---:|---:|---:|---:|---:|---:|
| Open Eyes | 0.1793 | 0.4610 | 0.3650 | 0.0428 | 0.2894 | 0.4247 |
| Partial Closure | 0.1786 | 0.3092 | 0.2202 | 0.0223 | 0.1852 | 0.2649 |
| Closed Eyes | 0.0338 | 0.0905 | 0.0608 | 0.0104 | 0.0469 | 0.0821 |

## Provisional calibrated mapping

For a future closure estimate, use the open and closed baselines rather than a
fixed EAR threshold:

```text
closure = clamp((open_baseline - current_openness)
                / (open_baseline - closed_baseline), 0, 1)
```

Using the collected means, the partial-closure estimate is
`47.6%` of the open-to-closed range. This is only a calibration
check; it is not direct measurement of 80% eyelid or pupil coverage.
