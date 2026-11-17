# Configuration

`default.yaml` contains application-level runtime settings shared by the
production modules. Paths are relative to the repository root and no
machine-specific or secret values belong in this directory.

The configuration loader validates positive dimensions, confidence values in
`[0, 1]`, the CPU MediaPipe delegate, and positive temporal durations.
Mathematical constants that define an algorithm remain close to the relevant
implementation when they are not runtime settings.
