# Temporal Decision Engine

## Purpose

The temporal decision engine evaluates the timing and repetition of
off-reference glances. It does not create events, store history, or replace
the gaze classifier.

The current implementation is
[`src/drivesense/visual_distraction/temporal.py`](../src/drivesense/visual_distraction/temporal.py).

## Processing flow

```text
Gaze Classification
    -> Gaze Assessment
    -> Glance Tracker
    -> Glance History
    -> Temporal Distraction Analyzer
```

- `GlanceTracker` opens and closes off-reference events.
- `GlanceHistory` stores completed events without automatic deletion.
- `TemporalDistractionAnalyzer` evaluates completed events and the currently
  active event.

## Prototype timing criteria

The current configuration uses:

| Criterion | Value |
|---|---:|
| Long glance | `>= 3 s` |
| Cumulative off-reference time | `>= 10 s` |
| Cumulative window | `30 s` |
| Re-engagement reset | `>= 2 s` continuously on reference |

When an event crosses a window boundary, only its overlapping duration is
counted. The active event is counted separately and is not added again as a
completed event.

These values are engineering criteria inspired by examples from Euro NCAP and
related research. They are not universal thresholds and do not prove driver
distraction.

## Output states

- `POTENTIAL_DISTRACTION`: a prototype temporal criterion was met.
- `ATTENTIVE`: the current assessment is on reference and no temporal
  criterion is active.
- `UNDETERMINED`: the available state is not sufficient for a conclusion.
- `UNAVAILABLE`: the current assessment cannot be made.

`UNAVAILABLE` must never be treated as `ATTENTIVE`.

## Known boundaries

The engine does not yet include a production driving-region model, traffic
context, vehicle state, or a final alert policy. Results require validation
with representative drivers and controlled scenarios.