"""Tests for the Persona Fusion Engine."""

import pytest
from src.personas.fusion_engine import FusionEngine, PersonaWeights, FusedResponse
from src.personas.persona_base import PersonaResponse
from src.personas.ash import Ash
from src.personas.sol import Sol
from src.personas.echo import Echo
from src.personas.kai import Kai
from src.personas.myra import Myra


class TestPersonaWeights:
    def test_defaults_are_zero(self):
        w = PersonaWeights()
        assert w.total() == 0.0

    def test_as_dict(self):
        w = PersonaWeights(ash=0.5, sol=0.3)
        d = w.as_dict()
        assert d["ash"] == 0.5
        assert d["sol"] == 0.3
        assert d["echo"] == 0.0

    def test_from_dict(self):
        w = PersonaWeights.from_dict({"ash": 0.7, "kai": 0.4})
        assert w.ash == 0.7
        assert w.kai == 0.4
        assert w.myra == 0.0

    def test_clamp(self):
        w = PersonaWeights(ash=1.5, sol=-0.3)
        w.clamp()
        assert w.ash == 1.0
        assert w.sol == 0.0

    def test_normalised_sums_to_one(self):
        w = PersonaWeights(ash=0.6, sol=0.4, echo=0.2)
        n = w.normalised()
        assert abs(sum(n.values()) - 1.0) < 0.001

    def test_normalised_all_zero(self):
        w = PersonaWeights()
        n = w.normalised()
        assert all(v == 0.0 for v in n.values())


class TestIndividualPersonas:
    def test_ash_meltdown_supportive(self):
        ash = Ash()
        resp = ash.generate_response({"distress_type": "meltdown"}, "supportive")
        assert resp.persona_id == "ash"
        assert len(resp.text) > 0
        assert resp.tone_tag == "supportive"

    def test_sol_cant_do_tasks_directive(self):
        sol = Sol()
        resp = sol.generate_response({"distress_type": "cant_do_tasks"}, "directive")
        assert resp.persona_id == "sol"
        assert len(resp.text) > 0

    def test_echo_self_blame_therapeutic(self):
        echo = Echo()
        resp = echo.generate_response({"distress_type": "self_blame"}, "therapeutic")
        assert resp.persona_id == "echo"
        assert len(resp.text) > 0

    def test_kai_hyperfocus_minimal(self):
        kai = Kai()
        resp = kai.generate_response({"distress_type": "hyperfocus_loop"}, "minimal")
        assert resp.persona_id == "kai"
        assert len(resp.text) > 0

    def test_myra_shutdown_triggers_silent(self):
        myra = Myra()
        resp = myra.generate_response({"distress_type": "shutdown"}, "supportive")
        assert resp.persona_id == "myra"
        assert resp.silent_mode is True
        assert "palette" in resp.visual_cues

    def test_myra_non_shutdown_is_not_silent(self):
        myra = Myra()
        resp = myra.generate_response({"distress_type": "meltdown"}, "supportive")
        assert resp.silent_mode is False

    def test_all_personas_have_default(self):
        for PersonaCls in [Ash, Sol, Echo, Kai, Myra]:
            p = PersonaCls()
            resp = p.generate_response({"distress_type": "unknown"}, "supportive")
            assert len(resp.text) > 0


class TestFusionEngine:
    def test_meltdown_weights_produce_ash_primary(self):
        engine = FusionEngine()
        weights = PersonaWeights(ash=0.9, sol=0.1, echo=0.2, kai=0.0, myra=0.8)
        fused = engine.fuse(weights, {"distress_type": "meltdown"})
        assert fused.primary_persona == "ash"
        assert len(fused.primary_text) > 0

    def test_shutdown_produces_silent_mode(self):
        engine = FusionEngine()
        weights = PersonaWeights(ash=0.0, sol=0.0, echo=0.0, kai=0.0, myra=1.0)
        fused = engine.fuse(weights, {"distress_type": "shutdown"})
        assert fused.primary_persona == "myra"
        assert fused.silent_mode is True

    def test_zero_weights_fallback_silent(self):
        engine = FusionEngine()
        weights = PersonaWeights()
        fused = engine.fuse(weights, {"distress_type": "meltdown"})
        assert fused.silent_mode is True

    def test_otoi_caps_respected(self):
        engine = FusionEngine()
        weights = PersonaWeights(ash=0.9, sol=0.5, echo=0.3, kai=0.1, myra=0.2)
        caps = {"ash": 0.1, "sol": 0.5, "echo": 0.3, "kai": 0.1, "myra": 0.2}
        fused = engine.fuse(weights, {"distress_type": "meltdown"}, otoi_caps=caps)
        assert fused.weights_used["ash"] <= fused.weights_used["sol"] + 0.01

    def test_all_contributing_personas_present(self):
        engine = FusionEngine()
        weights = PersonaWeights(ash=0.5, sol=0.5, echo=0.5, kai=0.5, myra=0.5)
        fused = engine.fuse(weights, {"distress_type": "meltdown"})
        assert len(fused.persona_contributions) == 5
        assert len(fused.all_suggested_actions) > 0

    def test_fuse_with_each_tone(self):
        engine = FusionEngine()
        weights = PersonaWeights(ash=0.8, myra=0.5)
        for tone in ["supportive", "minimal", "directive", "therapeutic"]:
            fused = engine.fuse(weights, {"distress_type": "meltdown"}, tone=tone)
            assert fused.primary_text != ""
