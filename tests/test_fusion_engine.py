"""Tests for the Persona Fusion Engine and individual personas."""

import pytest

from src.models import DistressInput, PersonaName, PersonaWeights, ToneProfile
from src.personas.ash import AshPersona
from src.personas.sol import SolPersona
from src.personas.echo import EchoPersona
from src.personas.kai import KaiPersona
from src.personas.myra import MyraPersona
from src.personas.fusion_engine import FusionEngine, DISTRESS_WEIGHT_MAP
from src.toi.governance import GovernanceMiddleware


# ---------------------------------------------------------------------------
# Individual persona tests
# ---------------------------------------------------------------------------

class TestAsh:
    def test_supportive(self):
        r = AshPersona().generate({}, ToneProfile.SUPPORTIVE, 0.8)
        assert r.persona == PersonaName.ASH
        assert "rest" in r.message.lower() or "pause" in r.message.lower()

    def test_minimal(self):
        r = AshPersona().generate({}, ToneProfile.MINIMAL, 0.5)
        assert len(r.message.split()) < 20


class TestSol:
    def test_supportive(self):
        r = SolPersona().generate({}, ToneProfile.SUPPORTIVE, 0.85)
        assert r.persona == PersonaName.SOL
        assert "step" in r.message.lower() or "task" in r.message.lower() or "thing" in r.message.lower()

    def test_directive(self):
        r = SolPersona().generate({}, ToneProfile.DIRECTIVE, 0.85)
        assert "timer" in r.message.lower() or "pick" in r.message.lower()


class TestEcho:
    def test_supportive(self):
        r = EchoPersona().generate({}, ToneProfile.SUPPORTIVE, 0.85)
        assert r.persona == PersonaName.ECHO

    def test_therapeutic(self):
        r = EchoPersona().generate({}, ToneProfile.THERAPEUTIC, 0.85)
        assert "?" in r.message


class TestKai:
    def test_supportive(self):
        r = KaiPersona().generate({}, ToneProfile.SUPPORTIVE, 0.85)
        assert r.persona == PersonaName.KAI

    def test_directive(self):
        r = KaiPersona().generate({}, ToneProfile.DIRECTIVE, 0.85)
        assert "stop" in r.message.lower() or "loop" in r.message.lower() or "action" in r.message.lower()


class TestMyra:
    def test_supportive(self):
        r = MyraPersona().generate({}, ToneProfile.SUPPORTIVE, 1.0)
        assert r.persona == PersonaName.MYRA
        assert "here" in r.message.lower()

    def test_silent_mode(self):
        r = MyraPersona().generate({"silent_mode": True}, ToneProfile.MINIMAL, 1.0)
        assert r.metadata.get("silent_mode") is True
        assert r.metadata.get("no_timers") is True


# ---------------------------------------------------------------------------
# Distress-to-weight mapping
# ---------------------------------------------------------------------------

class TestDistressWeightMap:
    def test_meltdown_weights(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.MELTDOWN]
        assert w.ash >= 0.7
        assert w.myra >= 0.7

    def test_task_paralysis_weights(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.TASK_PARALYSIS]
        assert w.sol >= 0.8

    def test_self_blame_weights(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.SELF_BLAME]
        assert w.echo >= 0.8

    def test_hyperfocus_loop_weights(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.HYPERFOCUS_LOOP]
        assert w.kai >= 0.8

    def test_shutdown_weights(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.SHUTDOWN]
        assert w.myra >= 1.0
        assert w.sol == 0.0


# ---------------------------------------------------------------------------
# FusionEngine integration
# ---------------------------------------------------------------------------

class TestFusionEngine:
    @pytest.fixture()
    def engine(self):
        gm = GovernanceMiddleware({"tone": "supportive"})
        return FusionEngine(gm)

    def test_meltdown_response(self, engine):
        resp = engine.generate(DistressInput.MELTDOWN)
        assert resp.primary_message
        assert resp.silent_mode is False

    def test_shutdown_triggers_silent(self, engine):
        resp = engine.generate(DistressInput.SHUTDOWN)
        assert resp.silent_mode is True
        assert len(resp.persona_contributions) == 1
        assert resp.persona_contributions[0].persona == PersonaName.MYRA

    def test_task_paralysis_includes_sol(self, engine):
        resp = engine.generate(DistressInput.TASK_PARALYSIS)
        personas = {c.persona for c in resp.persona_contributions}
        assert PersonaName.SOL in personas

    def test_weight_override(self, engine):
        custom = PersonaWeights(ash=0.0, sol=0.0, echo=0.0, kai=0.0, myra=1.0)
        resp = engine.generate(DistressInput.MELTDOWN, weight_override=custom)
        personas = {c.persona for c in resp.persona_contributions}
        assert personas == {PersonaName.MYRA}

    def test_resolve_weights(self, engine):
        w = engine.resolve_weights(DistressInput.SELF_BLAME)
        assert w.echo >= 0.8
