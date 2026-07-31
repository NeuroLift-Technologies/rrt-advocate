"""Conformance port of ``test/keywordLayer.test.ts`` from
``@neurolift-technologies/rrt-advocate`` (the source of truth)."""
import math

from rrt_advocate import KeywordLayer, KeywordSemanticField

layer = KeywordLayer()


def test_returns_empty_result_for_blank_input():
    r = layer.analyze("   ")
    assert r.detected_fields == []
    assert r.confidence_score == 0
    assert r.self_harm_detected is False
    assert r.primary_field is None


def test_detects_self_harm_risk_and_forces_confidence_to_1():
    r = layer.analyze("honestly I want to kill myself")
    assert r.self_harm_detected is True
    assert KeywordSemanticField.SELF_HARM_RISK in r.detected_fields
    assert r.confidence_score == 1.0
    assert r.primary_field is KeywordSemanticField.SELF_HARM_RISK


def test_detects_a_single_overwhelm_field_with_its_base_weight():
    r = layer.analyze("I can't cope with this")
    assert KeywordSemanticField.OVERWHELM in r.detected_fields
    assert r.self_harm_detected is False
    assert math.isclose(r.confidence_score, 0.15, abs_tol=5e-6)


def test_detects_negative_self_talk():
    r = layer.analyze("i hate myself so much right now")
    assert KeywordSemanticField.NEGATIVE_SELF_TALK in r.detected_fields
    assert math.isclose(r.confidence_score, 0.15, abs_tol=5e-6)


def test_compounds_confidence_across_multiple_distinct_fields():
    # OVERWHELM (0.15) + MELTDOWN (0.25) = 0.40 (no repeats -> no count bonus)
    r = layer.analyze("everything is falling apart and I can't cope")
    assert KeywordSemanticField.MELTDOWN in r.detected_fields
    assert KeywordSemanticField.OVERWHELM in r.detected_fields
    assert math.isclose(r.confidence_score, 0.4, abs_tol=5e-6)


def test_fails_open_on_apostrophe_free_dictation_input():
    # "can't cope" dictated as "cant cope" must still fire OVERWHELM.
    assert KeywordSemanticField.OVERWHELM in layer.analyze("i cant cope").detected_fields
    # "i don't deserve" dictated as "i dont deserve".
    assert (
        KeywordSemanticField.NEGATIVE_SELF_TALK
        in layer.analyze("i dont deserve this").detected_fields
    )
    # "i'm not good enough" dictated as "im not good enough".
    assert (
        KeywordSemanticField.NEGATIVE_SELF_TALK
        in layer.analyze("im not good enough honestly").detected_fields
    )
    # Smart-quote apostrophe (U+2019) must behave identically to ASCII.
    assert KeywordSemanticField.OVERWHELM in layer.analyze("i can’t cope").detected_fields


def test_caps_compounded_confidence_at_1():
    r = layer.analyze(
        "i hate myself, everything is falling apart, i can't cope, i can't start, "
        "i can't stop thinking about it, i feel completely numb"
    )
    assert r.confidence_score <= 1.0
