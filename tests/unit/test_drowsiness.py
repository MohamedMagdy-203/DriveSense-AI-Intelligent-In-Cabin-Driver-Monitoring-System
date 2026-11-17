import pytest

from drivesense.drowsiness.metrics import (
    PerclosWindow,
    calibrated_closure_score,
)


def test_calibrated_closure_score_preserves_clamping() -> None:
    assert calibrated_closure_score(0.3298, 0.3298, 0.0736) == 0.0
    assert calibrated_closure_score(0.0736, 0.3298, 0.0736) == 1.0
    assert calibrated_closure_score(0.2, 0.3298, 0.0736) == pytest.approx(
        (0.3298 - 0.2) / (0.3298 - 0.0736)
    )


def test_perclos_window_uses_timestamp_segments() -> None:
    window = PerclosWindow(1000)
    window.update(0, False)
    window.update(500, True)
    result = window.update(1000, False)

    assert result == pytest.approx(50.0)
