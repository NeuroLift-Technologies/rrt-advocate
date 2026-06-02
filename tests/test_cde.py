"""
Tests for the 3-Layer Crisis Detection Engine (CDE).
"""
import asyncio
import pytest
import pytest_asyncio
from crisis.detectors.keyword_layer import (
    KeywordLayer,
    KeywordSemanticField,
    KeywordAnalysisResult,
)
from crisis.detectors.sentiment_layer import SentimentLayer, SentimentAnalysisResult
from crisis.detectors.behavioral_layer import BehavioralLayer, BehavioralAnalysisResult
from crisis.detectors.crisis_detector import CrisisDetector, CrisisIndicators
from crisis.assessors.crisis_assessor import CrisisAssessor, CrisisLevel


class TestKeywordLayer:
    def setup_method(self):
        self.layer = KeywordLayer()

    def test_empty_text_returns_zero_confidence(self):
        result = self.layer.analyze("")
        assert result.confidence_score == 0.0
        assert result.detected_fields == []

    def test_negative_self_talk_detection(self):
        result = self.layer.analyze("I hate myself, I'm so worthless")
        assert KeywordSemanticField.NEGATIVE_SELF_TALK in result.detected_fields
        assert result.confidence_score > 0

    def test_task_avoidance_detection(self):
        result = self.layer.analyze("I just can't start anything today, totally paralyzed")
        assert KeywordSemanticField.TASK_AVOIDANCE in result.detected_fields

    def test_overwhelm_detection(self):
        result = self.layer.analyze("Everything is too much, I'm completely drowning")
        assert KeywordSemanticField.OVERWHELM in result.detected_fields

    def test_meltdown_detection(self):
        result = self.layer.analyze("I'm having a complete meltdown right now")
        assert KeywordSemanticField.MELTDOWN in result.detected_fields

    def test_shutdown_detection(self):
        result = self.layer.analyze("I've completely shut down, just gone numb")
        assert KeywordSemanticField.SHUTDOWN in result.detected_fields

    def test_hyperfocus_loop_detection(self):
        result = self.layer.analyze("I keep going down the rabbit hole, can't stop obsessing")
        assert KeywordSemanticField.HYPERFOCUS_LOOP in result.detected_fields

    def test_self_harm_risk_returns_max_confidence(self):
        result = self.layer.analyze("I don't want to be here anymore, better off without me")
        assert result.self_harm_detected is True
        assert result.confidence_score == 1.0

    def test_self_harm_detection_sets_flag(self):
        result = self.layer.analyze("thinking about ending it all")
        assert result.self_harm_detected is True

    def test_neutral_text_low_confidence(self):
        result = self.layer.analyze("The weather is nice today, I'm going for a walk.")
        assert result.confidence_score < 0.15
        assert result.self_harm_detected is False

    def test_multiple_fields_compound_confidence(self):
        result_single = self.layer.analyze("I hate myself")
        result_multi = self.layer.analyze(
            "I hate myself, I'm having a complete meltdown, everything is too much, I can't start anything"
        )
        assert result_multi.confidence_score > result_single.confidence_score

    def test_primary_field_identified(self):
        result = self.layer.analyze("I'm completely melting down, falling apart")
        assert result.primary_field is not None

    def test_has_field_method(self):
        result = self.layer.analyze("I hate myself, I'm worthless")
        assert result.has_field(KeywordSemanticField.NEGATIVE_SELF_TALK) is True
        assert result.has_field(KeywordSemanticField.MELTDOWN) is False


class TestSentimentLayer:
    def setup_method(self):
        self.layer = SentimentLayer(window_size=5)

    def test_very_negative_text_high_confidence(self):
        result = self.layer.analyze("I hate everything, I'm a complete failure, nothing works")
        assert result.current_reading.compound < 0
        assert result.confidence_score > 0

    def test_positive_text_low_confidence(self):
        result = self.layer.analyze("I feel good today, things are going well")
        assert result.confidence_score == 0.0 or result.confidence_score < 0.1

    def test_window_trend_detection(self):
        # Add several negative messages
        for msg in [
            "I'm doing okay",
            "Starting to feel a bit off",
            "Really struggling now",
            "I can't cope at all",
            "Everything is terrible",
        ]:
            result = self.layer.analyze(msg)
        assert result.trend in ("declining", "sharply_declining", "stable")

    def test_reset_window(self):
        self.layer.analyze("terrible day")
        self.layer.analyze("awful")
        self.layer.reset_window()
        result = self.layer.analyze("neutral text")
        assert len(result.window_readings) == 1

    def test_analysis_returns_correct_type(self):
        result = self.layer.analyze("some text")
        assert isinstance(result, SentimentAnalysisResult)
        assert hasattr(result, "current_reading")
        assert hasattr(result, "trend")
        assert hasattr(result, "confidence_score")


class TestBehavioralLayer:
    def setup_method(self):
        self.layer = BehavioralLayer(window_size=5)

    def test_first_message_no_latency(self):
        result = self.layer.analyze("hello")
        assert result.response_latency is None

    def test_looping_detection(self):
        # Send the same message repeatedly
        self.layer.analyze("I can't stop thinking about this")
        self.layer.analyze("I can't stop thinking about this loop")
        self.layer.analyze("I can't stop thinking about this again")
        result = self.layer.analyze("I can't stop thinking about this")
        assert result.looping_detected is True or result.looping_similarity > 0.3

    def test_short_message_low_complexity(self):
        result = self.layer.analyze("ok")
        assert result.message_complexity < 0.3

    def test_long_message_higher_complexity(self):
        long_msg = " ".join(["I'm really struggling with everything today and"] * 5)
        result = self.layer.analyze(long_msg)
        assert result.message_complexity > 0.5

    def test_fragmenting_trend_detection(self):
        self.layer.analyze(" ".join(["word"] * 30))
        self.layer.analyze(" ".join(["word"] * 25))
        self.layer.analyze(" ".join(["word"] * 15))
        self.layer.analyze(" ".join(["word"] * 5))
        result = self.layer.analyze("ok")
        assert result.complexity_trend in ("simplifying", "fragmenting")

    def test_reset_clears_history(self):
        self.layer.analyze("message one")
        self.layer.analyze("message two")
        self.layer.reset()
        result = self.layer.analyze("fresh start")
        assert result.response_latency is None

    def test_analysis_returns_correct_type(self):
        result = self.layer.analyze("test message")
        assert isinstance(result, BehavioralAnalysisResult)


@pytest.mark.asyncio
class TestCrisisDetector:
    async def test_detect_indicators_empty_message(self):
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators("")
        assert isinstance(indicators, CrisisIndicators)
        assert indicators.aggregate_confidence == 0.0

    async def test_detect_indicators_high_distress(self):
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators(
            "I hate myself, I'm having a meltdown, can't cope with anything"
        )
        assert indicators.aggregate_confidence > 0.1
        assert len(indicators.detected_semantic_fields) > 0

    async def test_self_harm_escalates_to_max_confidence(self):
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators(
            "I don't want to be here anymore"
        )
        assert indicators.self_harm_risk is True
        assert indicators.aggregate_confidence == 1.0

    async def test_neutral_message_low_confidence(self):
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators(
            "Going to the grocery store later today."
        )
        assert indicators.aggregate_confidence < 0.2

    async def test_indicators_has_all_layer_scores(self):
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators("I'm struggling a bit")
        assert hasattr(indicators, "layer1_confidence")
        assert hasattr(indicators, "layer2_confidence")
        assert hasattr(indicators, "layer3_confidence")
        assert hasattr(indicators, "aggregate_confidence")

    async def test_session_reset(self):
        detector = CrisisDetector()
        await detector.detect_crisis_indicators("message one")
        detector.reset_session()
        indicators = await detector.detect_crisis_indicators("fresh start")
        assert indicators is not None


@pytest.mark.asyncio
class TestCrisisAssessor:
    async def test_green_level_for_low_confidence(self):
        assessor = CrisisAssessor("test_user")
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators("I'm doing okay today.")
        assessment = await assessor.assess_crisis(indicators)
        assert assessment.crisis_level == CrisisLevel.GREEN

    async def test_black_level_for_self_harm(self):
        assessor = CrisisAssessor("test_user")
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators("I don't want to be here anymore")
        assessment = await assessor.assess_crisis(indicators)
        assert assessment.crisis_level == CrisisLevel.BLACK

    async def test_assessment_has_required_fields(self):
        assessor = CrisisAssessor("test_user")
        detector = CrisisDetector()
        indicators = await detector.detect_crisis_indicators("struggling a bit")
        assessment = await assessor.assess_crisis(indicators)
        assert hasattr(assessment, "crisis_level")
        assert hasattr(assessment, "confidence_score")
        assert hasattr(assessment, "user_safety_score")
        assert hasattr(assessment, "recommended_interventions")

    async def test_safety_score_range(self):
        assessor = CrisisAssessor("test_user")
        detector = CrisisDetector()
        for msg in ["I'm fine", "I'm struggling", "I can't cope", "I want to hurt myself"]:
            indicators = await detector.detect_crisis_indicators(msg)
            assessment = await assessor.assess_crisis(indicators)
            assert 0.0 <= assessment.user_safety_score <= 1.0
