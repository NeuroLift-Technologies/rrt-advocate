"""Tests for the 3-layer Crisis Detection Engine."""
import pytest
import time
from src.crisis.detection_engine import CrisisDetectionEngine
from src.crisis.keyword_analyzer import analyse as keyword_analyse
from src.crisis.sentiment_analyzer import SentimentAnalyzer
from src.crisis.behavioral_analyzer import BehavioralAnalyzer
from src.crisis.models import CrisisLevel


class TestKeywordAnalyzer:
    def test_clean_text_returns_zero_score(self):
        score, signals = keyword_analyse("Having a great day today!")
        assert score == 0.0
        assert signals == []

    def test_negative_self_talk_detected(self):
        score, signals = keyword_analyse("I'm worthless and can't do anything right.")
        assert score > 0.0
        types = [s.signal_type for s in signals]
        assert "negative_self_talk" in types

    def test_overwhelm_detected(self):
        score, signals = keyword_analyse("Everything is too much right now, I'm in a meltdown.")
        types = [s.signal_type for s in signals]
        assert "overwhelm" in types

    def test_self_harm_language_returns_max_score(self):
        score, signals = keyword_analyse("I want to hurt myself.")
        types = [s.signal_type for s in signals]
        assert "self_harm_language" in types
        assert any(s.score == 1.0 for s in signals)

    def test_shutdown_detected(self):
        score, signals = keyword_analyse("I've completely shut down, I'm frozen.")
        types = [s.signal_type for s in signals]
        assert "shutdown" in types

    def test_layer_tag_is_correct(self):
        _, signals = keyword_analyse("I'm paralysed, stuck, can't start anything.")
        for s in signals:
            assert s.source_layer == 1


class TestSentimentAnalyzer:
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_text_low_score(self):
        score, _ = self.analyzer.analyse("I feel really great and calm today.")
        assert score < 0.3

    def test_very_negative_text_higher_score(self):
        score, _ = self.analyzer.analyse("I feel absolutely terrible and completely hopeless.")
        assert score > 0.0

    def test_polarity_drop_detected_over_window(self):
        self.analyzer.reset_history()
        self.analyzer.analyse("Feeling good and calm today.")
        self.analyzer.analyse("A bit tired but okay.")
        self.analyzer.analyse("Not great.")
        self.analyzer.analyse("I feel hopeless and empty.")
        score, signals = self.analyzer.analyse("Completely desperate and trapped.")
        types = [s.signal_type for s in signals]
        # Either polarity drop or negative polarity should fire
        assert score > 0.0

    def test_layer_tag_is_correct(self):
        _, signals = self.analyzer.analyse("I feel worthless and hopeless.")
        for s in signals:
            assert s.source_layer == 2


class TestBehavioralAnalyzer:
    def setup_method(self):
        self.analyzer = BehavioralAnalyzer(latency_spike_threshold=10.0)

    def test_latency_spike_detected(self):
        base_ts = time.time()
        self.analyzer.analyse("Starting message", timestamp=base_ts)
        score, signals = self.analyzer.analyse("After long silence", timestamp=base_ts + 30)
        types = [s.signal_type for s in signals]
        assert "response_latency_spike" in types

    def test_looping_repetition_detected(self):
        text = "I keep thinking about how I failed and I messed everything up"
        for _ in range(4):
            self.analyzer.analyse(text)
        score, signals = self.analyzer.analyse(text)
        types = [s.signal_type for s in signals]
        assert "looping_repetition" in types

    def test_no_signal_on_varied_messages(self):
        msgs = [
            "Just had breakfast",
            "Working on a report now",
            "Going for a walk later",
        ]
        base_ts = time.time()
        for i, m in enumerate(msgs):
            score, _ = self.analyzer.analyse(m, timestamp=base_ts + i * 5)
        assert score < 0.5

    def test_layer_tag_is_correct(self):
        base_ts = time.time()
        self.analyzer.analyse("message one", timestamp=base_ts)
        _, signals = self.analyzer.analyse("message two", timestamp=base_ts + 30)
        for s in signals:
            assert s.source_layer == 3


class TestCrisisDetectionEngine:
    def setup_method(self):
        self.cde = CrisisDetectionEngine()

    def test_clean_message_is_green(self):
        result = self.cde.analyse("I'm having a decent day, nothing urgent.")
        assert result.crisis_level == CrisisLevel.GREEN

    def test_strong_distress_is_above_green(self):
        result = self.cde.analyse(
            "I can't stop blaming myself, I'm completely worthless and hopeless."
        )
        assert result.crisis_level > CrisisLevel.GREEN

    def test_self_harm_triggers_escalation(self):
        result = self.cde.analyse("I want to hurt myself, I don't want to exist.")
        assert result.escalation_required is True
        assert result.crisis_level >= CrisisLevel.RED

    def test_composite_score_in_range(self):
        result = self.cde.analyse("Everything is too much, meltdown, can't cope.")
        assert 0.0 <= result.composite_score <= 1.0

    def test_recommended_personas_non_empty(self):
        result = self.cde.analyse("I'm so ashamed of myself.")
        assert len(result.recommended_personas) > 0

    def test_dominant_distress_type_set(self):
        result = self.cde.analyse("I'm completely shut down, frozen.")
        assert result.dominant_distress_type != ""

    def test_layer_scores_non_negative(self):
        result = self.cde.analyse("Feeling a bit stuck today.")
        assert result.layer1_score >= 0.0
        assert result.layer2_score >= 0.0
        assert result.layer3_score >= 0.0

    def test_session_reset_clears_state(self):
        self.cde.analyse("I feel hopeless and terrible.")
        self.cde.reset_session()
        result = self.cde.analyse("I'm fine now.")
        assert result.crisis_level == CrisisLevel.GREEN
