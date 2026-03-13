"""Tests for the TOI-OTOI Governance Wrapper."""

import pytest
from src.toi.toi_config import (
    TOIConfig,
    TonePreference,
    PacingPreference,
    CognitiveScaffoldingLevel,
    SafetyBoundary,
)
from src.toi.toi_parser import TOIParser, TOIFilterResult
from src.toi.otoi_coordinator import OTOICoordinator, PersonaDirective


class TestTOIConfig:
    def test_defaults(self):
        toi = TOIConfig()
        assert toi.tone == TonePreference.SUPPORTIVE
        assert toi.pacing == PacingPreference.USER_LED
        assert toi.cognitive_scaffolding == CognitiveScaffoldingLevel.MODERATE
        assert toi.safety_boundaries == []
        assert len(toi.allowed_personas) == 5

    def test_from_dict(self):
        data = {
            "tone": "minimal",
            "pacing": "fast",
            "cognitive_scaffolding": "heavy",
            "safety_boundaries": ["no_timers", "no_task_lists"],
            "allowed_personas": ["ash", "myra"],
        }
        toi = TOIConfig.from_dict(data)
        assert toi.tone == TonePreference.MINIMAL
        assert toi.pacing == PacingPreference.FAST
        assert SafetyBoundary.NO_TIMERS in toi.safety_boundaries
        assert toi.persona_allowed("ash") is True
        assert toi.persona_allowed("sol") is False

    def test_to_dict_roundtrip(self):
        original = TOIConfig(
            tone=TonePreference.DIRECTIVE,
            safety_boundaries=[SafetyBoundary.NO_PRODUCTIVITY_FRAMING],
        )
        d = original.to_dict()
        restored = TOIConfig.from_dict(d)
        assert restored.tone == original.tone
        assert restored.safety_boundaries == original.safety_boundaries

    def test_boundary_active(self):
        toi = TOIConfig(safety_boundaries=[SafetyBoundary.SILENT_MODE_ONLY])
        assert toi.boundary_active(SafetyBoundary.SILENT_MODE_ONLY) is True
        assert toi.boundary_active(SafetyBoundary.NO_TIMERS) is False


class TestTOIParser:
    def test_no_modifications_on_clean_text(self):
        toi = TOIConfig()
        parser = TOIParser(toi)
        result = parser.filter_response("You're doing great today.")
        assert result.filtered_text == "You're doing great today."
        assert result.modifications == []

    def test_strips_productivity_framing(self):
        toi = TOIConfig(safety_boundaries=[SafetyBoundary.NO_PRODUCTIVITY_FRAMING])
        parser = TOIParser(toi)
        result = parser.filter_response("You should be more productive today.")
        assert "productive" not in result.filtered_text.lower()
        assert "removed_productivity_framing" in result.modifications

    def test_strips_timer_references(self):
        toi = TOIConfig(safety_boundaries=[SafetyBoundary.NO_TIMERS])
        parser = TOIParser(toi)
        result = parser.filter_response("Let's set a timer for 10 minutes.")
        assert "set a timer" not in result.filtered_text.lower()

    def test_strips_task_list_references(self):
        toi = TOIConfig(safety_boundaries=[SafetyBoundary.NO_TASK_LISTS])
        parser = TOIParser(toi)
        result = parser.filter_response("Here's a to-do list for you.")
        assert "to-do list" not in result.filtered_text.lower()

    def test_softens_unsolicited_advice(self):
        toi = TOIConfig(safety_boundaries=[SafetyBoundary.NO_UNSOLICITED_ADVICE])
        parser = TOIParser(toi)
        result = parser.filter_response("You should take a break.")
        assert "you should" not in result.filtered_text.lower()
        assert "softened_unsolicited_advice" in result.modifications

    def test_silent_mode_blocks_all(self):
        toi = TOIConfig(safety_boundaries=[SafetyBoundary.SILENT_MODE_ONLY])
        parser = TOIParser(toi)
        result = parser.filter_response("Some response text")
        assert result.blocked is True
        assert result.filtered_text == ""

    def test_truncates_long_messages(self):
        toi = TOIConfig(max_message_length=20)
        parser = TOIParser(toi)
        result = parser.filter_response("This is a longer message than twenty characters")
        assert len(result.filtered_text) <= 25  # allows for ellipsis rounding
        assert "truncated_to_max_length" in result.modifications

    def test_validates_persona_access(self):
        toi = TOIConfig(allowed_personas=["ash", "myra"])
        parser = TOIParser(toi)
        assert parser.validate_persona_access("ash") is True
        assert parser.validate_persona_access("sol") is False


class TestOTOICoordinator:
    def test_generates_directives_for_all_personas(self):
        toi = TOIConfig()
        otoi = OTOICoordinator(toi)
        weights = {"ash": 0.8, "sol": 0.5, "echo": 0.6, "kai": 0.3, "myra": 0.7}
        directives = otoi.generate_directives(weights)
        assert len(directives) == 5
        assert all(d.permitted for d in directives)

    def test_blocks_disallowed_personas(self):
        toi = TOIConfig(allowed_personas=["ash", "myra"])
        otoi = OTOICoordinator(toi)
        weights = {"ash": 0.8, "sol": 0.5, "echo": 0.6, "kai": 0.3, "myra": 0.7}
        directives = otoi.generate_directives(weights)
        sol_directive = next(d for d in directives if d.persona_id == "sol")
        assert sol_directive.permitted is False
        assert sol_directive.weight_cap == 0.0

    def test_silent_mode_only_myra(self):
        toi = TOIConfig(safety_boundaries=[SafetyBoundary.SILENT_MODE_ONLY])
        otoi = OTOICoordinator(toi)
        weights = {"ash": 0.8, "sol": 0.5, "echo": 0.6, "kai": 0.3, "myra": 0.7}
        directives = otoi.generate_directives(weights)
        for d in directives:
            if d.persona_id != "myra":
                assert d.weight_cap == 0.0

    def test_validate_fusion_clips_weights(self):
        toi = TOIConfig(allowed_personas=["ash"])
        otoi = OTOICoordinator(toi)
        raw = {"ash": 0.9, "sol": 0.5, "echo": 0.5, "kai": 0.5, "myra": 0.5}
        validated = otoi.validate_fusion_output(raw)
        assert validated["sol"] == 0.0
        assert validated["ash"] > 0
