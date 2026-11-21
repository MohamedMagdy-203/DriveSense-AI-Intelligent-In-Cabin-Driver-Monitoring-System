# Drowsiness Detection

## Scope

DriveSense AI currently provides reusable metrics for eye-closure analysis. It
does not yet claim a complete or clinically validated drowsiness classifier.
The live experiments use MediaPipe Face Landmarker landmarks and run on the
CPU in the tested Windows environment.

## Current signals

- Eye openness and calibrated closure score.
- Blink duration and prolonged eye closure.
- PERCLOS over a rolling time window.

The reusable implementation is in
[`src/drivesense/drowsiness/metrics.py`](../src/drivesense/drowsiness/metrics.py).
Camera-dependent demonstrations remain under
[`experiments/face_landmarker/eye_closure/`](../experiments/face_landmarker/eye_closure/).

## Implemented calculations

### Calibrated closure score

The openness value is mapped to a clamped score in `[0, 1]`:

```text
score = clamp((open_baseline - openness) /
              (open_baseline - closed_baseline), 0, 1)
```

The open baseline must be greater than the closed baseline. Invalid baseline
ordering raises an error.

### PERCLOS

`PerclosWindow` stores timestamped observed segments and calculates the
percentage of observed time marked as closed inside the configured rolling
window. Missing observations reset continuity and are not treated as closed.

## Measured experiment results

The latest eye-openness calibration produced:

- Open mean: `0.3033`
- Partial mean: `0.1928`
- Closed mean: `0.0816`

The latest eye-closure run recorded:

- Blinks: `6`
- Prolonged closures: `1`
- Average blink duration: `189.50 ms`
- Longest closure: `2576 ms`

These are results from one local run, not population-level validation.

## Limitations

- No final drowsiness decision or alert policy is implemented.
- Thresholds remain prototype parameters and require evaluation across users,
  lighting conditions, camera positions, and frame-loss scenarios.
- A missing face or missing landmark observation must not be interpreted as
  evidence of drowsiness.

## References

- Åkerstedt T, Gillberg M. Subjective and Objective Sleepiness in the Active
  Individual. International Journal of Neuroscience. 1990;52:29-37.
  DOI: https://doi.org/10.3109/00207459008994241
- Kaida K et al. Validation of the Karolinska sleepiness scale against
  performance and EEG variables. Clinical Neurophysiology. 2006;117:1574-1581.
  DOI: https://doi.org/10.1016/j.clinph.2006.03.011
- Dinges DF, Grace R. PERCLOS: A Valid Psychophysiological Measure of
  Alertness as Assessed by Psychomotor Vigilance Tasks. Federal Highway
  Administration report FHWA-MCRT-98-006, 1998.

These sources support sleepiness/PERCLOS concepts. They do not validate the
project's 60-second PERCLOS window, 0.8 closure score, or 4-second test
scenario across real drivers.