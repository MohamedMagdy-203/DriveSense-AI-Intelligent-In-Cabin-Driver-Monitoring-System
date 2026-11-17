from drivesense.visual_distraction.assessment import assess_driving_gaze
from drivesense.visual_distraction.glance_history import GlanceHistory
from drivesense.visual_distraction.glance_tracker import GlanceTracker
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


def test_gaze_to_temporal_pipeline(monkeypatch) -> None:
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
    tracker = GlanceTracker()
    history = GlanceHistory()
    analyzer = TemporalDistractionAnalyzer()

    center = assess_driving_gaze(
        GazeClassification(GazeDirection.CENTER, (eye,)),
        head,
    )
    tracker.update(center.gaze_status)
    assert analyzer.update(
        history,
        tracker.active_start_time,
        center.gaze_status,
    ).status is DistractionStatus.ATTENTIVE

    clock[0] = 100.1
    off_reference = assess_driving_gaze(
        GazeClassification(GazeDirection.LEFT, (eye,)),
        head,
    )
    tracker.update(off_reference.gaze_status)
    clock[0] = 101.0
    tracker.update(off_reference.gaze_status)
    clock[0] = 102.0
    event = tracker.update(center.gaze_status)
    assert event is not None
    history.add(event)

    assert analyzer.update(
        history,
        tracker.active_start_time,
        center.gaze_status,
    ).status is DistractionStatus.ATTENTIVE
