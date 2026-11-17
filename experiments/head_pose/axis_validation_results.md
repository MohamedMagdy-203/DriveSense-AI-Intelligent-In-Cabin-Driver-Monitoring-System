# Head Pose Axis and Sign Validation

This report analyzes every matrix in `motion_frames.csv`. The Neutral reference is the mean of all recorded Neutral matrices.

For each frame:

```text
R_relative = R_neutral.T @ R_current
rotation_vector = log(R_relative)
```

The matrix scale is removed before calculating the relative rotation. Rotation-vector components are reported in degrees and are not named Yaw, Pitch, or Roll.

- Input matrices: `410`
- Output vectors: `410`
- Per-frame vectors: `motion_rotation_vectors.csv`

## Neutral

- Frames: `89`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | -0.03 | -0.16 | +0.27 |
| Y | +0.02 | -0.15 | +0.20 |
| Z | +0.01 | -0.22 | +0.22 |

- Expected sign: `N/A` for the Neutral reference.

## Turn Left

- Frames: `85`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | -1.67 | -3.01 | -0.23 |
| Y | +54.87 | +53.37 | +55.94 |
| Z | -15.15 | -16.18 | -14.40 |

- Expected sign: `Z negative`; preserved in `98.82%` of frames.

## Turn Right

- Frames: `58`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | -7.58 | -9.37 | -4.54 |
| Y | -48.03 | -57.60 | -23.04 |
| Z | +19.09 | +5.58 | +22.84 |

- Expected sign: `Z positive`; preserved in `100.00%` of frames.

## Look Up

- Frames: `89`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | -40.57 | -46.05 | -39.56 |
| Y | -4.57 | -4.89 | -4.19 |
| Z | -5.16 | -5.76 | -4.28 |

- Expected sign: `X negative`; preserved in `100.00%` of frames.

## Look Down

- Frames: `89`

| Component | Median (deg) | P10 (deg) | P90 (deg) |
|---|---:|---:|---:|
| X | +25.96 | +25.18 | +26.63 |
| Y | -0.12 | -0.80 | +0.44 |
| Z | -3.13 | -3.97 | -2.38 |

- Expected sign: `X positive`; preserved in `100.00%` of frames.
