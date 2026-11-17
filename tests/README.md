# Tests

The test suite uses `pytest` and keeps ordinary tests independent of camera
hardware. Unit tests cover configuration validation, gaze geometry and
classification, head-pose history, and visual-distraction state transitions.
The integration test exercises the complete gaze-to-temporal pipeline with a
deterministic monotonic clock.

Run all tests with:

```bash
./.venv/Scripts/python.exe -m pytest
```
