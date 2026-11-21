# Configuration

`default.yaml` contains application-level runtime settings shared by the
production modules. Paths are relative to the repository root and no
machine-specific or secret values belong in this directory.

The configuration loader validates positive dimensions, confidence values in
`[0, 1]`, the CPU MediaPipe delegate, and positive temporal durations.
Mathematical constants that define an algorithm remain close to the relevant
implementation when they are not runtime settings.

The `temporal` section contains visual-distraction prototype durations:
`3` seconds for a long glance and `10/30` seconds for cumulative glance time.

The `drowsiness` section contains PERCLOS window and eye-openness mapping
values. `prolonged_closure_test_seconds: 4.0` is an evaluation scenario for
continuous closure, not a universal microsleep definition. KSS 7/8 values are
not configured as EAR or PERCLOS thresholds.
