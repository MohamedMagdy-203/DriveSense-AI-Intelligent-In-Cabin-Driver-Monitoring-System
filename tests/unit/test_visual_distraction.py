from drivesense.visual_distraction.assessment import (
    GazeAssessmentStatus,
    assess_driving_gaze,
)
from drivesense.visual_distraction.glance_history import GlanceHistory
from drivesense.visual_distraction.glance_tracker import GlanceEvent, GlanceTracker
from drivesense.visual_distraction.temporal import (
    DistractionStatus,
    TemporalDistractionAnalyzer,
)
from drivesense.visual_distraction.gaze.classification import (
    EyeGazeClassification,
    GazeClassification,
    GazeDirection,
)
from drivesense.head_pose.pose import HeadPoseEstimate, HeadPoseStatus


def test_glance_tracker_closes_and_history_returns_overlapping_events(monkeypatch) -> None:
    timestamps = iter((10.0, 12.0))
    monkeypatch.setattr(
        "drivesense.visual_distraction.glance_tracker.time.monotonic",
        lambda: next(timestamps),
    )
    tracker = GlanceTracker()
    history = GlanceHistory()

    assert tracker.update(GazeAssessmentStatus.OFF_REFERENCE) is None
    event = tracker.update(GazeAssessmentStatus.ON_REFERENCE)
    assert event == GlanceEvent(10.0, 12.0, 2.0)
    history.add(event)

    assert history.get_recent(11.0, 11.5) == (event,)


def test_pipeline_reports_active_long_glance(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(
        "drivesense.visual_distraction.glance_tracker.time.monotonic",
        lambda: clock[0],
    )
    monkeypatch.setattr(
        "drivesense.visual_distraction.temporal.time.monotonic",
        lambda: clock[0],
    )
    eye = EyeGazeClassification(
        "right_eye",
        GazeDirection.CENTER,
        GazeDirection.CENTER,
        0.0,
        0.0,
    )
    head = HeadPoseEstimate(HeadPoseStatus.OK, 0.0, 0.0, 0.0, 0.0)
    gaze = GazeClassification(GazeDirection.LEFT, (eye,))
    assessment = assess_driving_gaze(gaze, head)
    tracker = GlanceTracker()
    history = GlanceHistory()
    analyzer = TemporalDistractionAnalyzer()

    tracker.update(assessment.gaze_status)
    clock[0] = 103.0
    result = analyzer.update(
        history,
        tracker.active_start_time,
        assessment.gaze_status,
    )

    assert result.status is DistractionStatus.POTENTIAL_DISTRACTION
