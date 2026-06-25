"""Conformance port of ``test/behavioralLayer.test.ts`` from
``@neurolift-technologies/rrt-advocate`` (the source of truth)."""
import math

from rrt_advocate import BehavioralLayer


def test_returns_a_zeroed_result_for_blank_input():
    r = BehavioralLayer().analyze("   ")
    assert r.message_complexity == 0
    assert r.looping_detected is False
    assert r.response_latency is None
    assert r.metrics.word_count == 0


def test_computes_a_normalized_complexity_score():
    # 15 words, one sentence -> word_score=0.5, sentence_score=1.0 -> 0.7
    text = (
        "alpha bravo charlie delta echo foxtrot golf hotel india juliet "
        "kilo lima mike november oscar"
    )
    r = BehavioralLayer().analyze(text)
    assert r.metrics.word_count == 15
    assert math.isclose(r.message_complexity, 0.7, abs_tol=5e-6)
    assert r.complexity_trend == "normal"


def test_detects_looping_on_a_repeated_message():
    layer = BehavioralLayer()
    text = "thinking about the same worry again and again right now"
    first = layer.analyze(text)
    assert first.looping_detected is False
    second = layer.analyze(text)
    assert math.isclose(second.looping_similarity, 1.0, abs_tol=5e-6)
    assert second.looping_detected is True
    assert math.isclose(second.confidence_score, 0.2, abs_tol=5e-6)


def test_detects_a_fragmenting_complexity_trend():
    layer = BehavioralLayer()
    layer.analyze(
        "alpha bravo charlie delta echo foxtrot golf hotel india juliet "
        "kilo lima mike november oscar"
    )
    layer.analyze("uniform victor whiskey xray yankee zulu")
    r = layer.analyze("done finished")
    assert r.complexity_trend == "fragmenting"


def test_resets_session_state():
    layer = BehavioralLayer()
    layer.analyze("thinking about the same worry again and again right now")
    layer.reset()
    r = layer.analyze("thinking about the same worry again and again right now")
    assert r.looping_detected is False
