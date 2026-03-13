"""Tests for the TOI parser and OTOI coordinator."""
import pytest
from src.toi.toi_parser import TOIParser
from src.toi.models import ToneProfile, PacingMode, TOIConfig, InteractionContract
from src.toi.otoi_coordinator import OTOICoordinator
from src.personas.models import PersonaWeights


class TestTOIParser:
    def setup_method(self):
        self.parser = TOIParser()

    def test_from_dict_defaults(self):
        cfg = self.parser.from_dict({"user_id": "u1"})
        assert cfg.user_id == "u1"
        assert cfg.tone_profile == ToneProfile.SUPPORTIVE_DEFAULT
        assert cfg.pacing == PacingMode.STANDARD
        assert cfg.cognitive_scaffolding.chunking_enabled is True
        assert cfg.safety_boundaries.no_productivity_pressure is True

    def test_from_dict_tone_profile(self):
        cfg = self.parser.from_dict({"user_id": "u2", "tone_profile": "minimal"})
        assert cfg.tone_profile == ToneProfile.MINIMAL

    def test_from_dict_unknown_tone_defaults_gracefully(self):
        cfg = self.parser.from_dict({"user_id": "u3", "tone_profile": "nonexistent"})
        assert cfg.tone_profile == ToneProfile.SUPPORTIVE_DEFAULT

    def test_persona_mute_list(self):
        cfg = self.parser.from_dict({"user_id": "u4", "persona_mute_list": ["SOL", "KAI"]})
        assert cfg.is_persona_allowed("ASH") is True
        assert cfg.is_persona_allowed("SOL") is False
        assert cfg.is_persona_allowed("KAI") is False

    def test_validate_all_muted_warns(self):
        cfg = self.parser.from_dict({
            "user_id": "u5",
            "persona_mute_list": ["ASH", "SOL", "ECHO", "KAI", "MYRA"]
        })
        concerns = self.parser.validate(cfg)
        assert any("All five" in c for c in concerns)

    def test_validate_clean_config_no_concerns(self):
        cfg = self.parser.from_dict({"user_id": "u6"})
        assert self.parser.validate(cfg) == []


class TestOTOICoordinator:
    def setup_method(self):
        self.coord = OTOICoordinator()
        self.parser = TOIParser()

    def _make_contract(self, tone: str = "supportive_default", muted=None, preferred=None) -> InteractionContract:
        import uuid
        toi = self.parser.from_dict({
            "user_id": "test",
            "tone_profile": tone,
            "persona_mute_list": muted or [],
            "preferred_personas": preferred or [],
        })
        return InteractionContract(toi=toi, session_id=str(uuid.uuid4()), consent_granted=True)

    def test_produce_directive_minimal_tone_limits_personas(self):
        contract = self._make_contract(tone="minimal")
        weights = PersonaWeights(ash=0.5, sol=0.1, echo=0.1, kai=0.1, myra=0.2)
        directive = self.coord.produce_directive(contract, weights)
        assert directive.max_personas_per_response == 1

    def test_produce_directive_respects_mute_list(self):
        contract = self._make_contract(muted=["ASH", "ECHO", "KAI"])
        weights = PersonaWeights(ash=0.5, sol=0.2, echo=0.1, kai=0.1, myra=0.1)
        directive = self.coord.produce_directive(contract, weights)
        assert "ASH" not in directive.permitted_personas
        assert "ECHO" not in directive.permitted_personas

    def test_produce_directive_shutdown_triggers_silence(self):
        contract = self._make_contract()
        weights = PersonaWeights(ash=0.1, sol=0.1, echo=0.1, kai=0.1, myra=0.6)
        directive = self.coord.produce_directive(contract, weights, distress_type="shutdown")
        assert directive.silence_requested is True

    def test_no_productivity_pressure_guard(self):
        contract = self._make_contract()
        dirty = "You should complete your task and get it done by tomorrow."
        cleaned = self.coord.check_no_productivity_pressure(contract, dirty)
        assert "get it done" not in cleaned

    def test_consent_checkpoint_flagged_when_not_consented(self):
        import uuid
        toi = self.parser.from_dict({"user_id": "t"})
        contract = InteractionContract(toi=toi, session_id=str(uuid.uuid4()), consent_granted=False)
        weights = PersonaWeights(myra=1.0)
        directive = self.coord.produce_directive(contract, weights)
        assert directive.consent_checkpoint_required is True
