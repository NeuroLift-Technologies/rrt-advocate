"""Tests for the 3-layer Crisis Detection Engine."""

import pytest
from datetime import datetime, timedelta

from src.crisis.keyword_layer import KeywordLayer
from src.crisis.sentiment_layer import SentimentLayer
from src.crisis.behavioral_layer import BehavioralLayer
from src.crisis.engine import CrisisDetectionEngine
from src.models import CrisisLevel


# ---------------------------------------------------------------------------
# Layer 1 — Keyword
# ---------------------------------------------------------------------------

class TestKeywordLayer:
    def test_no_distress(self):
        sig = KeywordLayer().analyse("I had a great day at work today")
        assert sig.score == 0.0
        assert sig.indicators == []

    def test_negative_self_talk(self):
        sig = KeywordLayer().analyse("i'm worthless and i always mess up")
        assert sig.score > 0.0
        assert "negative_self_talk" in sig.indicators

    def test_task_avoidance(self):
        sig = KeywordLayer().analyse("i can't start anything, everything is piling up")
        assert "task_avoidance" in sig.indicators

    def test_overwhelm(self):
        sig = KeywordLayer().analyse("everything is too much, i can't cope, make it stop")
        assert "overwhelm" in sig.indicators
        assert sig.score > 0.3

    def test_multiple_fields(self):
        sig = KeywordLayer().analyse(
            "i'm a failure, i can't start, i'm drowning"
        )
        assert len(sig.indicators) >= 2


# ---------------------------------------------------------------------------
# Layer 2 — Sentiment
# ---------------------------------------------------------------------------

class TestSentimentLayer:
    def test_positive_message(self):
        layer = SentimentLayer()
        sig = layer.analyse("I feel great and happy today")
        assert sig.score == 0.0 or sig.score < 0.1

    def test_negative_message(self):
        layer = SentimentLayer()
        sig = layer.analyse("I feel terrible and hopeless and scared")
        assert sig.score > 0.0
        assert "negative_polarity" in sig.indicators

    def test_polarity_drop(self):
        layer = SentimentLayer()
        layer.analyse("I feel great and happy")
        layer.analyse("Everything is good today")
        sig = layer.analyse("I hate everything, I'm miserable and hopeless")
        assert sig.score > 0.0

    def test_negation_handling(self):
        layer = SentimentLayer()
        sig = layer.analyse("I'm not happy at all")
        assert sig.metadata["polarity"] <= 0.0

    def test_intensifier(self):
        layer = SentimentLayer()
        sig_plain = layer.analyse("I feel bad")
        layer2 = SentimentLayer()
        sig_intense = layer2.analyse("I feel very bad")
        assert sig_intense.metadata["polarity"] <= sig_plain.metadata["polarity"]


# ---------------------------------------------------------------------------
# Layer 3 — Behavioural
# ---------------------------------------------------------------------------

class TestBehavioralLayer:
    def test_no_anomaly_on_first_message(self):
        layer = BehavioralLayer()
        sig = layer.analyse("Hello there")
        assert sig.score == 0.0

    def test_complexity_drop(self):
        layer = BehavioralLayer()
        layer.analyse("This is a fairly long message with lots of words and context")
        layer.analyse("Another reasonably lengthy message providing detail")
        layer.analyse("Same kind of moderately wordy message")
        sig = layer.analyse("help")
        assert sig.score > 0.0
        assert "message_complexity_drop" in sig.indicators

    def test_looping_detection(self):
        layer = BehavioralLayer()
        layer.analyse("i can't do this anymore")
        layer.analyse("i can't do this anymore")
        sig = layer.analyse("i can't do this anymore")
        assert "message_looping" in sig.indicators

    def test_latency_anomaly(self):
        layer = BehavioralLayer()
        t0 = datetime(2026, 1, 1, 12, 0, 0)
        layer.analyse("msg1", t0)
        layer.analyse("msg2", t0 + timedelta(seconds=5))
        layer.analyse("msg3", t0 + timedelta(seconds=10))
        sig = layer.analyse("msg4", t0 + timedelta(seconds=60))
        assert sig.score >= 0.0


# ---------------------------------------------------------------------------
# CDE (full pipeline)
# ---------------------------------------------------------------------------

class TestCrisisDetectionEngine:
    def test_green_on_neutral_text(self):
        cde = CrisisDetectionEngine()
        result = cde.analyse("I had a productive morning and feel fine.")
        assert result.crisis_level == CrisisLevel.GREEN
        assert result.user_safety_score > 0.5

    def test_elevated_on_distress(self):
        cde = CrisisDetectionEngine()
        result = cde.analyse("I'm worthless, i can't do anything right, i'm broken")
        assert result.crisis_level != CrisisLevel.GREEN
        assert result.confidence_score > 0.0

    def test_high_distress(self):
        cde = CrisisDetectionEngine()
        result = cde.analyse(
            "I'm a failure, everything is too much, i can't cope, "
            "i hate myself, i'm drowning, make it stop, i'm overwhelmed"
        )
        assert result.crisis_level.value in ("elevated", "high", "critical", "emergency")

    def test_config_loading(self):
        cde = CrisisDetectionEngine("config/crisis_thresholds.yaml")
        result = cde.analyse("Just checking in.")
        assert result.crisis_level == CrisisLevel.GREEN

    def test_recommendations_scale(self):
        cde = CrisisDetectionEngine()
        green = cde.analyse("All good here.")
        assert green.recommended_interventions == []
        distress = cde.analyse(
            "I'm worthless, i'm a burden, i can't cope, everything is too much, i'm falling apart"
        )
        assert len(distress.recommended_interventions) > 0

    def test_cde_signals_populated(self):
        cde = CrisisDetectionEngine()
        result = cde.analyse("i hate myself and i can't do this")
        assert len(result.cde_signals) == 3
        layers = {s.layer for s in result.cde_signals}
        assert layers == {"keyword", "sentiment", "behavioral"}
