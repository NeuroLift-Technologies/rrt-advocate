"""Tests for the Configurable Tone Profiles."""

from src.models import ToneProfile
from src.tone.profiles import ToneProfileManager, TONE_REGISTRY


class TestToneProfileManager:
    def test_all_four_profiles_registered(self):
        profiles = ToneProfileManager.all_profiles()
        assert len(profiles) == 4
        for tp in ToneProfile:
            assert tp in profiles

    def test_get_returns_correct_spec(self):
        spec = ToneProfileManager.get(ToneProfile.MINIMAL)
        assert spec.profile == ToneProfile.MINIMAL
        assert spec.max_sentence_count == 2

    def test_system_preamble(self):
        preamble = ToneProfileManager.system_preamble(ToneProfile.DIRECTIVE)
        assert "action" in preamble.lower()

    def test_guardrails(self):
        rails = ToneProfileManager.guardrails(ToneProfile.THERAPEUTIC)
        assert "diagnose" in rails.lower()

    def test_ideal_personas(self):
        spec = ToneProfileManager.get(ToneProfile.SUPPORTIVE)
        assert "ash" in spec.ideal_personas
        assert "myra" in spec.ideal_personas

    def test_directive_ideal_personas(self):
        spec = ToneProfileManager.get(ToneProfile.DIRECTIVE)
        assert "sol" in spec.ideal_personas
        assert "kai" in spec.ideal_personas
