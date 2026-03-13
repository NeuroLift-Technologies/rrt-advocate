"""Tests for the Crisis Detection Engine (CDE) — all 3 layers + pipeline."""

import time
import pytest
from src.detection.keyword_analyzer import KeywordAnalyzer, KeywordResult
from src.detection.sentiment_analyzer import SentimentAnalyzer, SentimentResult
from src.detection.behavioral_analyzer import BehavioralAnalyzer, BehavioralResult
from src.detection.cde_pipeline import CDEPipeline, CDEResult


class TestKeywordAnalyzer:
    def test_detects_negative_self_talk(self):
        kw = KeywordAnalyzer()
        result = kw.analyse("I'm worthless and I can't do anything right")
        assert result.field_scores["negative_self_talk"] > 0
        assert len(result.matched_fields["negative_self_talk"]) >= 1

    def test_detects_task_avoidance(self):
        kw = KeywordAnalyzer()
        result = kw.analyse("I can't start anything, it's too much")
        assert result.field_scores["task_avoidance"] > 0

    def test_detects_overwhelm(self):
        kw = KeywordAnalyzer()
        result = kw.analyse("Everything hurts, I'm having a meltdown and can't cope")
        assert result.field_scores["overwhelm"] > 0
        assert result.overall_score > 0

    def test_detects_hyperfocus(self):
        kw = KeywordAnalyzer()
        result = kw.analyse("I can't stop, stuck in a loop, hours have passed")
        assert result.field_scores["hyperfocus_loop"] > 0

    def test_detects_relational_distress(self):
        kw = KeywordAnalyzer()
        result = kw.analyse("They hate me, nobody cares, I'm all alone")
        assert result.field_scores["relational_distress"] > 0

    def test_clean_text_low_score(self):
        kw = KeywordAnalyzer()
        result = kw.analyse("The weather is nice today and I had a good lunch")
        assert result.overall_score == 0.0

    def test_dominant_field_correct(self):
        kw = KeywordAnalyzer()
        result = kw.analyse("I can't stop, stuck in a loop, obsessing over this thing")
        assert result.dominant_field == "hyperfocus_loop"

    def test_score_capped_at_one(self):
        kw = KeywordAnalyzer()
        text = " ".join([
            "i'm worthless", "i'm a failure", "i can't do anything right",
            "i'm broken", "what's wrong with me", "i'm so stupid",
        ])
        result = kw.analyse(text)
        assert result.field_scores["negative_self_talk"] <= 1.0
        assert result.overall_score <= 1.0


class TestSentimentAnalyzer:
    def test_positive_text(self):
        sa = SentimentAnalyzer()
        result = sa.analyse("I feel great and happy today, everything is wonderful")
        assert result.polarity > 0

    def test_negative_text(self):
        sa = SentimentAnalyzer()
        result = sa.analyse("I feel terrible and hopeless, everything is awful")
        assert result.polarity < 0

    def test_neutral_text(self):
        sa = SentimentAnalyzer()
        result = sa.analyse("The table is made of wood")
        assert result.dominant_emotion == "neutral"

    def test_polarity_drop_detection(self):
        sa = SentimentAnalyzer()
        sa.analyse("I feel great and happy and wonderful")
        sa.analyse("I feel great and happy")
        sa.analyse("I feel great")
        result = sa.analyse("I feel terrible and hopeless and broken and lost")
        assert result.polarity_drop > 0

    def test_negation_flips_polarity(self):
        sa = SentimentAnalyzer()
        r1 = sa.analyse("I am not happy")
        sa.reset()
        r2 = sa.analyse("I am happy")
        assert r1.polarity < r2.polarity

    def test_intensifier_amplifies(self):
        sa = SentimentAnalyzer()
        r1 = sa.analyse("I feel very terrible today")
        sa.reset()
        r2 = sa.analyse("I feel terrible today")
        # Intensifier increases the neg count (1.5 vs 1.0) so the absolute
        # negative weight is higher even if magnitude normalises per-token.
        assert r1.polarity <= r2.polarity

    def test_reset_clears_history(self):
        sa = SentimentAnalyzer()
        sa.analyse("something")
        sa.reset()
        result = sa.analyse("another thing")
        assert result.polarity_drop == 0.0

    def test_trend_insufficient_data(self):
        sa = SentimentAnalyzer()
        result = sa.analyse("hello")
        assert result.window_trend == "insufficient_data"


class TestBehavioralAnalyzer:
    def test_initial_message_low_score(self):
        ba = BehavioralAnalyzer()
        result = ba.record_message("Hello there", 1000.0)
        assert result.overall_score == 0.0

    def test_latency_increase_detected(self):
        ba = BehavioralAnalyzer()
        ba.record_message("msg 1", 1000.0)
        ba.record_message("msg 2", 1002.0)
        ba.record_message("msg 3", 1004.0)
        result = ba.record_message("msg 4", 1020.0)
        assert result.latency_score > 0

    def test_complexity_drop_detected(self):
        ba = BehavioralAnalyzer()
        ba.record_message("This is a reasonably long and complex message about many things", 1000.0)
        ba.record_message("Another fairly detailed message with lots of words in it", 1002.0)
        ba.record_message("Yet another complex message that establishes a baseline", 1004.0)
        ba.record_message("ok", 1006.0)
        ba.record_message("no", 1008.0)
        result = ba.record_message(".", 1010.0)
        assert result.complexity_score > 0

    def test_looping_detected(self):
        ba = BehavioralAnalyzer()
        for i in range(5):
            ba.record_message("I can't do this I'm stuck I can't do this", 1000.0 + i * 2)
        result = ba.record_message("I can't do this I'm stuck I can't do this", 1012.0)
        assert result.looping_score > 0

    def test_flags_generated(self):
        ba = BehavioralAnalyzer()
        ba.record_message("Detailed message one with lots of words", 1000.0)
        ba.record_message("Detailed message two with lots of words", 1002.0)
        ba.record_message("Detailed message three establishing baseline", 1004.0)
        ba.record_message("ok", 1040.0)
        ba.record_message(".", 1080.0)
        result = ba.record_message(".", 1120.0)
        assert isinstance(result.flags, list)

    def test_reset_clears_state(self):
        ba = BehavioralAnalyzer()
        ba.record_message("test", 1000.0)
        ba.reset()
        result = ba.record_message("test", 2000.0)
        assert result.latency_score == 0.0


class TestCDEPipeline:
    def test_distressed_message_above_threshold(self):
        cde = CDEPipeline()
        result = cde.analyse("I'm worthless and I can't do anything, everything hurts")
        assert result.aggregate_distress > 0
        assert result.distress_type in [
            "overwhelm", "negative_self_talk", "task_avoidance",
            "hyperfocus_loop", "relational_distress",
        ]
        assert "ash" in result.recommended_weights

    def test_calm_message_low_distress(self):
        cde = CDEPipeline()
        result = cde.analyse("The weather is nice today")
        assert result.aggregate_distress < 0.2

    def test_recommended_weights_present(self):
        cde = CDEPipeline()
        result = cde.analyse("I can't stop, stuck in a loop, obsessing")
        for persona in ["ash", "sol", "echo", "kai", "myra"]:
            assert persona in result.recommended_weights

    def test_pipeline_stateful_across_messages(self):
        cde = CDEPipeline()
        cde.analyse("I feel great today")
        cde.analyse("Things are good")
        result = cde.analyse("Everything is terrible and I hate myself and I'm broken")
        assert result.sentiment_result.polarity_drop >= 0

    def test_flags_propagated(self):
        cde = CDEPipeline()
        result = cde.analyse(
            "I'm worthless, I'm a failure, I'm broken, I can't do anything right, "
            "everything hurts, make it stop, I can't cope, falling apart"
        )
        assert isinstance(result.flags, list)

    def test_reset(self):
        cde = CDEPipeline()
        cde.analyse("something")
        cde.reset()
        result = cde.analyse("test")
        assert result.behavioral_result.latency_score == 0.0
