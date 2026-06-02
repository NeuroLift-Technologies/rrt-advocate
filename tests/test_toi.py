"""
Tests for the TOI/OTOI Governance Layer.
"""
import pytest
from toi.toi_models import TOIConfig, ToneProfile, Pacing, OTOIState
from toi.toi_parser import TOIParser
from toi.otoi_middleware import OTOIMiddleware


class TestTOIModels:
    def test_default_toi_config(self):
        config = TOIConfig()
        assert config.tone_profile == ToneProfile.SUPPORTIVE_DEFAULT
        assert config.pacing == Pacing.STANDARD
        assert config.cognitive_scaffolding_level == 2
        assert config.consent_given is False
        assert config.allow_task_loops is False  # Anti-forced-productivity default

    def test_persona_exclusion(self):
        config = TOIConfig(excluded_personas=["Ash", "Kai"])
        assert config.persona_is_excluded("ash") is True
        assert config.persona_is_excluded("ASH") is True
        assert config.persona_is_excluded("sol") is False

    def test_persona_preference(self):
        config = TOIConfig(preferred_personas=["Myra"])
        assert config.persona_is_preferred("myra") is True
        assert config.persona_is_preferred("ash") is False

    def test_silent_mode_flag(self):
        config = TOIConfig(silent_mode_preferred=True)
        assert config.requires_silent_mode() is True

    def test_effective_max_length_defaults(self):
        assert TOIConfig(tone_profile=ToneProfile.MINIMAL).effective_max_length() == 50
        assert TOIConfig(tone_profile=ToneProfile.DIRECTIVE).effective_max_length() == 150
        assert TOIConfig(tone_profile=ToneProfile.THERAPEUTIC_REFLECTIVE).effective_max_length() == 250
        assert TOIConfig(tone_profile=ToneProfile.SUPPORTIVE_DEFAULT).effective_max_length() == 200

    def test_effective_max_length_override(self):
        config = TOIConfig(max_response_length=75)
        assert config.effective_max_length() == 75


class TestTOIParser:
    def test_parse_from_dict_defaults(self):
        parser = TOIParser(defaults_path="config/toi_defaults.yaml")
        config = parser.parse_from_dict(None)
        assert isinstance(config, TOIConfig)
        assert config.tone_profile == ToneProfile.SUPPORTIVE_DEFAULT
        assert config.allow_task_loops is False

    def test_parse_from_dict_overrides(self):
        parser = TOIParser(defaults_path="config/toi_defaults.yaml")
        config = parser.parse_from_dict({
            "tone_profile": "minimal",
            "pacing": "very_slow",
            "cognitive_scaffolding_level": 0,
            "consent_given": True,
        })
        assert config.tone_profile == ToneProfile.MINIMAL
        assert config.pacing == Pacing.VERY_SLOW
        assert config.cognitive_scaffolding_level == 0
        assert config.consent_given is True

    def test_parse_unknown_tone_profile_defaults(self):
        parser = TOIParser(defaults_path="config/toi_defaults.yaml")
        config = parser.parse_from_dict({"tone_profile": "nonexistent"})
        assert config.tone_profile == ToneProfile.SUPPORTIVE_DEFAULT

    def test_scaffolding_clamped(self):
        parser = TOIParser(defaults_path="config/toi_defaults.yaml")
        config = parser.parse_from_dict({"cognitive_scaffolding_level": 99})
        assert config.cognitive_scaffolding_level == 3
        config2 = parser.parse_from_dict({"cognitive_scaffolding_level": -5})
        assert config2.cognitive_scaffolding_level == 0


class TestOTOIMiddleware:
    def _make_middleware(self, **kwargs):
        config = TOIConfig(**kwargs)
        return OTOIMiddleware(config, session_id="test-session")

    def test_consent_starts_false(self):
        mw = self._make_middleware()
        assert mw.check_consent() is False

    def test_grant_consent(self):
        mw = self._make_middleware()
        mw.grant_consent()
        assert mw.check_consent() is True

    def test_silent_mode_activation(self):
        mw = self._make_middleware()
        assert mw.state.silent_mode_active is False
        mw.activate_silent_mode()
        assert mw.state.silent_mode_active is True

    def test_silent_mode_filter_long_response(self):
        mw = self._make_middleware()
        mw.activate_silent_mode()
        long_text = "This is a very long response that should be drastically truncated by the silent mode filter."
        result = mw.filter_response(long_text, "myra")
        # Silent mode should return a very short response
        assert len(result.split()) <= 10

    def test_forbidden_phrase_removal(self):
        mw = self._make_middleware(tone_profile=ToneProfile.SUPPORTIVE_DEFAULT)
        mw.grant_consent()
        text = "You should really just calm down and try harder."
        result = mw.filter_response(text, "ash")
        assert "calm down" not in result.lower() or "just" not in result.lower()

    def test_persona_exclusion_routing(self):
        mw = self._make_middleware(excluded_personas=["kai", "sol"])
        allowed = mw.validate_persona_routing(["ash", "sol", "kai", "myra"])
        assert "sol" not in allowed
        assert "kai" not in allowed
        assert "ash" in allowed
        assert "myra" in allowed

    def test_persona_exclusion_all_fallback_to_myra(self):
        mw = self._make_middleware(excluded_personas=["ash", "sol", "echo", "kai", "myra"])
        allowed = mw.validate_persona_routing(["ash", "sol", "echo"])
        assert allowed == ["myra"]

    def test_length_enforcement(self):
        mw = self._make_middleware(tone_profile=ToneProfile.MINIMAL)
        mw.grant_consent()
        # MINIMAL tone max is 50 words
        long_text = " ".join(["word"] * 100)
        result = mw.filter_response(long_text, "myra")
        assert len(result.split()) <= 55  # Small buffer for punctuation

    def test_task_loop_guard(self):
        mw = self._make_middleware(allow_task_loops=False)
        mw.grant_consent()
        text = "Step 1: start. Then, step 2. Finally, step 3."
        result = mw.filter_response(text, "sol")
        assert mw.state.toi_violations_blocked > 0

    def test_session_summary(self):
        mw = self._make_middleware()
        mw.grant_consent()
        summary = mw.get_session_summary()
        assert "session_id" in summary
        assert summary["consent_given"] is True
        assert summary["tone_profile"] == "supportive_default"
