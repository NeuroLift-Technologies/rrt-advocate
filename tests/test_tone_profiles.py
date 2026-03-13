"""Tests for the Configurable Tone Profiles system."""

import pytest
from src.tones.tone_profiles import ToneManager, ToneProfile, ToneType


class TestToneManager:
    def test_all_four_tones_available(self):
        tm = ToneManager()
        assert len(tm.available_tones) == 4
        for t in [ToneType.SUPPORTIVE, ToneType.MINIMAL, ToneType.DIRECTIVE, ToneType.THERAPEUTIC]:
            assert t in tm.available_tones

    def test_get_profile_by_enum(self):
        tm = ToneManager()
        profile = tm.get_profile(ToneType.SUPPORTIVE)
        assert profile.tone_type == ToneType.SUPPORTIVE
        assert profile.label == "Supportive Default"

    def test_get_profile_by_string(self):
        tm = ToneManager()
        profile = tm.get_profile("minimal")
        assert profile.tone_type == ToneType.MINIMAL

    def test_llm_directive_non_empty(self):
        tm = ToneManager()
        for tone in tm.available_tones:
            directive = tm.get_llm_directive(tone)
            assert len(directive) > 20

    def test_persona_affinity_has_all_five(self):
        tm = ToneManager()
        for tone in tm.available_tones:
            affinity = tm.get_persona_affinity(tone)
            for persona in ["ash", "sol", "echo", "kai", "myra"]:
                assert persona in affinity
                assert 0.0 <= affinity[persona] <= 1.0

    def test_supportive_favours_ash_myra(self):
        tm = ToneManager()
        a = tm.get_persona_affinity(ToneType.SUPPORTIVE)
        assert a["ash"] >= 0.9
        assert a["myra"] >= 0.9

    def test_directive_favours_sol_kai(self):
        tm = ToneManager()
        a = tm.get_persona_affinity(ToneType.DIRECTIVE)
        assert a["sol"] >= 0.9
        assert a["kai"] >= 0.9

    def test_therapeutic_favours_ash_echo(self):
        tm = ToneManager()
        a = tm.get_persona_affinity(ToneType.THERAPEUTIC)
        assert a["ash"] >= 0.9
        assert a["echo"] >= 0.9

    def test_register_custom_profile(self):
        tm = ToneManager()
        custom = ToneProfile(
            tone_type=ToneType.SUPPORTIVE,
            label="Custom Supportive",
            description="Custom override",
            max_sentence_length=15,
            vocabulary_level="simple",
            emotional_register="warm",
            llm_system_directive="Be nice.",
        )
        tm.register_profile(custom)
        assert tm.get_profile(ToneType.SUPPORTIVE).label == "Custom Supportive"

    def test_invalid_tone_raises(self):
        tm = ToneManager()
        with pytest.raises(ValueError):
            tm.get_profile("nonexistent")
