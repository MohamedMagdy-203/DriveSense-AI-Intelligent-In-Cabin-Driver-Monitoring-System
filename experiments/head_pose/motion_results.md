# Head Pose Per-Frame Matrix Recording

Each CSV row contains one `4x4` facial transformation matrix for the first detected face in one captured frame.

- Duration per pose: `3 seconds`
- Total recorded matrices: `355`
- CSV output: `motion_frames.csv`

| Pose | Recorded matrices |
|---|---:|
| Neutral | 90 |
| Turn Left | 14 |
| Turn Right | 73 |
| Look Up | 89 |
| Look Down | 89 |

The provisional angle labels and axis vectors shown during capture are diagnostic only. Axis order and signs require comparison of these per-frame recordings.
