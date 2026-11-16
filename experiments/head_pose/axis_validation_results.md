# Head Pose Axis and Sign Validation

This report analyzes every matrix in `motion_frames.csv`. The Neutral reference is the mean of all recorded Neutral matrices.

For each frame:

```text
R_relative = R_neutral.T @ R_current
rotation_vector = log(R_relative)
```

The matrix scale is removed before calculating the relative rotation. Rotation-vector components are reported in degrees and are not named Yaw, Pitch, or Roll.

- Input matrices: `355`
- Output vectors: `355`
- Per-frame vectors: `motion_rotation_vectors.csv`

## Neutral

- Frames: `90`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | -0.02 | -0.40 | +0.57 |
| Y | +0.00 | -0.20 | +0.18 |
| Z | +0.01 | -0.11 | +0.10 |

- Expected sign: `N/A` for the Neutral reference.

## Turn Left

- Frames: `14`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | +3.56 | +1.12 | +5.71 |
| Y | +39.57 | +24.87 | +49.23 |
| Z | -10.54 | -14.57 | -9.53 |

- Expected sign: `Z negative`; preserved in `100.00%` of frames.

## Turn Right

- Frames: `73`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | -2.90 | -6.43 | -0.85 |
| Y | -60.18 | -62.78 | -52.47 |
| Z | +15.89 | +13.98 | +18.92 |

- Expected sign: `Z positive`; preserved in `100.00%` of frames.

## Look Up

- Frames: `89`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | -26.35 | -26.70 | -25.75 |
| Y | -4.86 | -5.71 | -4.62 |
| Z | -1.75 | -2.01 | -1.47 |

- Expected sign: `X negative`; preserved in `100.00%` of frames.

## Look Down

- Frames: `89`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | +16.53 | +15.93 | +18.60 |
| Y | +0.97 | +0.49 | +1.45 |
| Z | -1.64 | -1.91 | -1.48 |

- Expected sign: `X positive`; preserved in `100.00%` of frames.
