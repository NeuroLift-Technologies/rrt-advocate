"""Conformance port of ``test/engine.test.ts`` from
``@neurolift-technologies/rrt-advocate`` (the source of truth)."""
import math

from rrt_advocate import CrisisDetector, CrisisEngine, CrisisLevel


def engine():
    # Force the deterministic sentiment fallback for all engine tests.
    return CrisisEngine("test-user", sentiment_analyzer=None)


# --- CrisisDetector aggregation ---------------------------------------------


def test_weights_layers_and_self_consistently_aggregates():
    detector = CrisisDetector(sentiment_analyzer=None)
    ind = detector.detect_crisis_indicators("everything is falling apart and I can't cope")
    assert ind.self_harm_risk is False
    expected = min(
        1.0,
        ind.layer1_confidence * 0.45
        + ind.layer2_confidence * 0.35
        + ind.layer3_confidence * 0.2,
    )
    assert math.isclose(ind.aggregate_confidence, expected, abs_tol=1e-10)


def test_forces_aggregate_confidence_to_1_on_self_harm_risk():
    detector = CrisisDetector(sentiment_analyzer=None)
    ind = detector.detect_crisis_indicators("i want to kill myself")
    assert ind.self_harm_risk is True
    assert ind.aggregate_confidence == 1.0
    assert "SELF_HARM_RISK" in ind.get_primary_indicators()


def test_surfaces_a_declining_sentiment_trend_as_a_primary_indicator():
    detector = CrisisDetector(sentiment_analyzer=None)
    ind = detector.detect_crisis_indicators("i feel hopeless and broken")
    assert "sentiment_trend:declining" in ind.get_primary_indicators()


# --- CrisisEngine.assess ----------------------------------------------------


def test_rates_a_benign_message_green_with_a_high_safety_score():
    a = engine().assess("just checking in, all good here today")
    assert a.crisis_level is CrisisLevel.GREEN
    assert math.isclose(a.user_safety_score, 1.0, abs_tol=5e-6)
    assert a.confidence_score < 0.2


def test_escalates_self_harm_to_black_with_bundled_emergency_interventions():
    a = engine().assess("i want to kill myself")
    assert a.crisis_level is CrisisLevel.BLACK
    assert math.isclose(a.user_safety_score, 0.05, abs_tol=5e-6)
    assert a.escalation_threshold == 1.0
    assert "SELF_HARM_RISK" in a.primary_indicators
    # Proves the vendored crisis_thresholds.yaml was loaded.
    assert a.recommended_interventions == [
        "emergency_stabilization",
        "professional_contact",
        "crisis_hotline",
        "immediate_safety_measures",
    ]
    assert a.context_factors["self_harm_risk"] is True


def test_clears_per_session_behavioral_state_on_reset():
    e = engine()
    e.detect("i keep repeating the exact same worried thought")
    looped = e.detect("i keep repeating the exact same worried thought")
    assert looped.looping_detected is True

    e.reset_session()

    after_reset = e.detect("i keep repeating the exact same worried thought")
    assert after_reset.looping_detected is False
