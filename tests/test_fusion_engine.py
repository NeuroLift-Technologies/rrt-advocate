"""Tests for the Persona Fusion Engine."""
import pytest
from src.personas.fusion_engine import FusionEngine
from src.personas.models import PersonaWeights, PERSONAS
from src.toi.toi_parser import TOIParser


class TestFusionEngine:
    def setup_method(self):
        self.engine = FusionEngine()
        self.parser = TOIParser()

    # --- Classification tests (distress type mapping) ---

    def test_meltdown_input_leads_ash_or_myra(self):
        blend = self.engine.compute("Everything hurts / Meltdown")
        assert blend.lead_persona.name in ("ASH", "MYRA")
        assert blend.distress_type == "meltdown"

    def test_task_paralysis_input_leads_sol(self):
        blend = self.engine.compute("Can't do basic tasks")
        assert blend.lead_persona.name == "SOL"
        assert blend.distress_type == "task_paralysis"

    def test_self_blame_input_leads_echo(self):
        blend = self.engine.compute("Can't stop self-blame")
        assert blend.lead_persona.name == "ECHO"
        assert blend.distress_type == "self_blame"

    def test_hyperfocus_input_leads_kai(self):
        blend = self.engine.compute("Stuck in hyperfocus/loop")
        assert blend.lead_persona.name == "KAI"
        assert blend.distress_type == "hyperfocus_loop"

    def test_shutdown_input_leads_myra(self):
        blend = self.engine.compute("Don't know / Shut down")
        assert blend.lead_persona.name == "MYRA"
        assert blend.distress_type == "shutdown"

    # --- Weight normalisation ---

    def test_weights_sum_to_one(self):
        blend = self.engine.compute("Can't stop self-blame")
        total = sum(blend.weights.as_dict().values())
        assert abs(total - 1.0) < 0.01

    def test_weights_all_non_negative(self):
        for distress in ("meltdown", "task_paralysis", "self_blame", "hyperfocus_loop", "shutdown"):
            blend = self.engine.compute(distress)
            for name, w in blend.weights.as_dict().items():
                assert w >= 0.0, f"{name} weight is negative for {distress}"

    # --- TOI preference boosting ---

    def test_preferred_persona_gets_boosted(self):
        toi = self.parser.from_dict({"user_id": "u", "preferred_personas": ["ECHO"]})
        blend_without = self.engine.compute("Can't stop self-blame")
        blend_with = self.engine.compute("Can't stop self-blame", toi_config=toi)
        assert blend_with.weights.echo >= blend_without.weights.echo

    def test_muted_persona_gets_zero_weight(self):
        toi = self.parser.from_dict({"user_id": "u", "persona_mute_list": ["SOL"]})
        blend = self.engine.compute("Can't do basic tasks", toi_config=toi)
        assert blend.weights.sol == 0.0

    # --- Semantic boosting ---

    def test_raw_text_shame_boosts_ash(self):
        blend_no_text = self.engine.compute("meltdown")
        blend_with_text = self.engine.compute("meltdown", raw_text="I feel so ashamed")
        assert blend_with_text.weights.ash >= blend_no_text.weights.ash

    # --- PersonaWeights helpers ---

    def test_ranked_returns_non_empty(self):
        w = PersonaWeights(ash=0.3, sol=0.1, echo=0.4, kai=0.1, myra=0.1)
        ranked = w.normalised().ranked()
        assert len(ranked) >= 1
        assert ranked[0] == "ECHO"

    def test_normalised_zero_weights_gives_equal_distribution(self):
        w = PersonaWeights()
        n = w.normalised()
        total = sum(n.as_dict().values())
        assert abs(total - 1.0) < 0.01

    # --- Blend rationale ---

    def test_rationale_contains_lead_persona(self):
        blend = self.engine.compute("Stuck in hyperfocus/loop")
        assert "KAI" in blend.rationale
