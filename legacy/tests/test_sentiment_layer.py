"""Conformance port of ``test/sentimentLayer.test.ts`` from
``@neurolift-technologies/rrt-advocate`` (the source of truth).

These are cross-implementation known-answer fixtures: the compound/confidence
values were produced by the deterministic TypeScript heuristic fallback and must
reproduce bit-close under Python."""
import math

from rrt_advocate import SentimentLayer


def make_layer():
    # Force the deterministic heuristic fallback by passing `None` (no VADER).
    return SentimentLayer(5, None)


def test_scores_clearly_positive_text_as_stable_with_no_crisis_confidence():
    r = make_layer().analyze("i feel good and calm")
    assert math.isclose(r.current_reading.compound, 0.5, abs_tol=5e-6)
    assert r.trend == "stable"
    assert r.confidence_score == 0


def test_flags_a_negative_first_message_as_declining():
    r = make_layer().analyze("i feel hopeless and broken")
    assert math.isclose(r.current_reading.compound, -0.5, abs_tol=5e-6)
    assert r.trend == "declining"
    assert math.isclose(r.confidence_score, 0.25, abs_tol=5e-6)


def test_detects_a_sharp_decline_across_the_window():
    layer = make_layer()
    layer.analyze("good great calm happy")
    r = layer.analyze("hopeless worthless broken depressed awful")
    assert math.isclose(r.current_reading.compound, -0.7143, abs_tol=5e-4)
    assert r.trend == "sharply_declining"
    assert math.isclose(r.confidence_score, 0.5, abs_tol=5e-6)


def test_detects_recovery_after_a_negative_reading():
    layer = make_layer()
    layer.analyze("hopeless broken")
    r = layer.analyze("good great calm happy relieved")
    assert r.trend == "recovering"
    assert r.confidence_score == 0


def test_scores_via_the_auto_detected_analyzer_without_throwing():
    # Default constructor auto-detects `vaderSentiment` (an optional dependency)
    # and otherwise uses the heuristic fallback. Either path must return a finite
    # compound and never throw.
    r = SentimentLayer().analyze("I am so happy and calm today")
    assert math.isfinite(r.current_reading.compound)
    assert r.current_reading.compound >= -1
    assert r.current_reading.compound <= 1


def test_resets_the_sliding_window():
    layer = make_layer()
    layer.analyze("hopeless broken")
    layer.reset_window()
    assert layer.get_window_summary()["readings_count"] == 0
