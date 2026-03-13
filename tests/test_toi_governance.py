"""Tests for the TOI-OTOI Governance Wrapper."""

import pytest

from src.models import PersonaName, PersonaResponse, PersonaWeights, TOIConfig, ToneProfile
from src.toi.toi_parser import TOIParser
from src.toi.otoi_coordinator import OTOICoordinator
from src.toi.governance import GovernanceMiddleware


# ---------------------------------------------------------------------------
# TOIParser
# ---------------------------------------------------------------------------

class TestTOIParser:
    def test_defaults(self):
        parser = TOIParser.from_dict({})
        cfg = parser.parse()
        assert cfg.tone == ToneProfile.SUPPORTIVE
        assert cfg.pacing == "adaptive"
        assert cfg.cognitive_scaffolding is True
        assert cfg.persona_overrides is None

    def test_minimal_tone(self):
        cfg = TOIParser.from_dict({"tone": "minimal"}).parse()
        assert cfg.tone == ToneProfile.MINIMAL

    def test_directive_tone(self):
        cfg = TOIParser.from_dict({"tone": "directive"}).parse()
        assert cfg.tone == ToneProfile.DIRECTIVE

    def test_therapeutic_tone(self):
        cfg = TOIParser.from_dict({"tone": "therapeutic"}).parse()
        assert cfg.tone == ToneProfile.THERAPEUTIC

    def test_unknown_tone_falls_back_to_supportive(self):
        cfg = TOIParser.from_dict({"tone": "aggressive"}).parse()
        assert cfg.tone == ToneProfile.SUPPORTIVE

    def test_pacing_validation(self):
        cfg = TOIParser.from_dict({"pacing": "warp-speed"}).parse()
        assert cfg.pacing == "adaptive"

    def test_persona_overrides_valid(self):
        cfg = TOIParser.from_dict({
            "persona_overrides": {"ash": 0.5, "sol": 0.3, "echo": 0.1, "kai": 0.05, "myra": 0.05}
        }).parse()
        assert cfg.persona_overrides is not None
        assert cfg.persona_overrides.ash == 0.5

    def test_persona_overrides_invalid_range(self):
        cfg = TOIParser.from_dict({
            "persona_overrides": {"ash": 5.0}
        }).parse()
        assert cfg.persona_overrides is None

    def test_safety_boundaries_merge(self):
        cfg = TOIParser.from_dict({
            "safety_boundaries": {"allow_emergency_contacts": False}
        }).parse()
        assert cfg.safety_boundaries["allow_emergency_contacts"] is False
        assert cfg.safety_boundaries["allow_external_escalation"] is True

    def test_config_property_caches(self):
        parser = TOIParser.from_dict({"tone": "minimal"})
        c1 = parser.config
        c2 = parser.config
        assert c1 is c2

    def test_from_yaml(self, tmp_path):
        p = tmp_path / "toi.yaml"
        p.write_text("tone: directive\npacing: slow\n")
        cfg = TOIParser.from_yaml(str(p)).parse()
        assert cfg.tone == ToneProfile.DIRECTIVE
        assert cfg.pacing == "slow"


# ---------------------------------------------------------------------------
# OTOICoordinator
# ---------------------------------------------------------------------------

def _sample_contributions():
    return [
        PersonaResponse(persona=PersonaName.ASH, weight=0.8, message="Ash says rest.", tone=ToneProfile.SUPPORTIVE),
        PersonaResponse(persona=PersonaName.MYRA, weight=0.8, message="Myra says safe.", tone=ToneProfile.SUPPORTIVE),
        PersonaResponse(persona=PersonaName.SOL, weight=0.05, message="Sol says step.", tone=ToneProfile.SUPPORTIVE),
    ]


class TestOTOICoordinator:
    def test_enforce_orders_by_weight(self):
        toi = TOIConfig(tone=ToneProfile.SUPPORTIVE)
        coord = OTOICoordinator(toi)
        weights = PersonaWeights(ash=0.8, sol=0.05, echo=0.0, kai=0.0, myra=0.8)
        result = coord.enforce(_sample_contributions(), weights)
        assert result.persona_contributions[0].persona in (PersonaName.ASH, PersonaName.MYRA)

    def test_enforce_clamps_ceiling(self):
        toi = TOIConfig(tone=ToneProfile.SUPPORTIVE)
        coord = OTOICoordinator(toi)
        weights = PersonaWeights(ash=1.0, sol=0.0, echo=0.0, kai=0.0, myra=0.0)
        result = coord.enforce(_sample_contributions(), weights)
        assert result.weights_used.ash <= 0.85

    def test_silent_mode(self):
        toi = TOIConfig(tone=ToneProfile.MINIMAL)
        coord = OTOICoordinator(toi)
        weights = PersonaWeights(ash=0.0, sol=0.0, echo=0.0, kai=0.0, myra=1.0)
        result = coord.enforce(_sample_contributions(), weights, silent_mode=True)
        assert result.silent_mode is True
        assert len(result.persona_contributions) == 1
        assert result.persona_contributions[0].persona == PersonaName.MYRA

    def test_tone_override(self):
        toi = TOIConfig(tone=ToneProfile.DIRECTIVE)
        coord = OTOICoordinator(toi)
        weights = PersonaWeights(ash=0.5, sol=0.5, echo=0.0, kai=0.0, myra=0.0)
        result = coord.enforce(_sample_contributions(), weights)
        for c in result.persona_contributions:
            assert c.tone == ToneProfile.DIRECTIVE

    def test_persona_override_from_toi(self):
        override = PersonaWeights(ash=0.1, sol=0.1, echo=0.1, kai=0.1, myra=0.6)
        toi = TOIConfig(tone=ToneProfile.SUPPORTIVE, persona_overrides=override)
        coord = OTOICoordinator(toi)
        weights = PersonaWeights(ash=0.9, sol=0.0, echo=0.0, kai=0.0, myra=0.0)
        result = coord.enforce(_sample_contributions(), weights)
        assert result.weights_used.myra == 0.6


# ---------------------------------------------------------------------------
# GovernanceMiddleware
# ---------------------------------------------------------------------------

class TestGovernanceMiddleware:
    def test_process(self):
        gm = GovernanceMiddleware({"tone": "therapeutic"})
        weights = PersonaWeights(ash=0.5, sol=0.5, echo=0.0, kai=0.0, myra=0.0)
        result = gm.process(_sample_contributions(), weights)
        assert result.tone == ToneProfile.THERAPEUTIC

    def test_update_toi(self):
        gm = GovernanceMiddleware()
        assert gm.toi.tone == ToneProfile.SUPPORTIVE
        gm.update_toi({"tone": "minimal"})
        assert gm.toi.tone == ToneProfile.MINIMAL

    def test_from_yaml(self, tmp_path):
        p = tmp_path / "toi.yaml"
        p.write_text("tone: directive\n")
        gm = GovernanceMiddleware.from_yaml(str(p))
        assert gm.toi.tone == ToneProfile.DIRECTIVE
