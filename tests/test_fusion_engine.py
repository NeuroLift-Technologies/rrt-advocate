"""
Tests for the Persona Fusion Engine.
"""
import pytest
from toi.toi_models import TOIConfig, ToneProfile
from personas.fusion_engine import (
    FusionEngine,
    PersonaWeights,
    DistressInput,
    DISTRESS_WEIGHT_MAP,
    EngineContext,
    BlendedResponse,
)
from personas.base_persona import PersonaContribution
from personas.ash import AshPersona
from personas.sol import SolPersona
from personas.echo import EchoPersona
from personas.kai import KaiPersona
from personas.myra import MyraPersona


class TestPersonaWeights:
    def test_default_weights_equal(self):
        w = PersonaWeights()
        assert w.ash == w.sol == w.echo == w.kai == w.myra == 0.2

    def test_normalize_sums_to_one(self):
        w = PersonaWeights(ash=0.45, myra=0.40, echo=0.10, sol=0.05, kai=0.00)
        n = w.normalize()
        total = n.ash + n.sol + n.echo + n.kai + n.myra
        assert abs(total - 1.0) < 0.001

    def test_normalize_zero_weights(self):
        w = PersonaWeights(ash=0.0, sol=0.0, echo=0.0, kai=0.0, myra=0.0)
        n = w.normalize()
        total = n.ash + n.sol + n.echo + n.kai + n.myra
        assert abs(total - 1.0) < 0.001

    def test_dominant_persona(self):
        w = PersonaWeights(ash=0.00, sol=0.65, echo=0.20, kai=0.10, myra=0.05)
        name, weight = w.dominant_persona()
        assert name == "sol"
        assert abs(weight - 0.65) < 0.001

    def test_active_personas_threshold(self):
        w = PersonaWeights(ash=0.45, myra=0.40, echo=0.10, sol=0.05, kai=0.00)
        active = w.active_personas(threshold=0.05)
        assert "ash" in active
        assert "myra" in active
        assert "echo" in active
        assert "sol" in active
        assert "kai" not in active

    def test_as_dict(self):
        w = PersonaWeights(ash=0.3, sol=0.3, echo=0.2, kai=0.1, myra=0.1)
        d = w.as_dict()
        assert set(d.keys()) == {"ash", "sol", "echo", "kai", "myra"}


class TestDistressWeightMap:
    """Verify the canonical distress input → weight mappings from the handoff spec."""

    def test_meltdown_weights_ash_myra_dominant(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.EVERYTHING_HURTS_MELTDOWN]
        assert w.ash >= 0.40
        assert w.myra >= 0.35
        assert w.kai == 0.0  # No Kai in meltdown

    def test_cant_task_weights_sol_dominant(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.CANT_DO_BASIC_TASKS]
        assert w.sol >= 0.60

    def test_self_blame_weights_echo_dominant(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.CANT_STOP_SELF_BLAME]
        assert w.echo >= 0.50

    def test_hyperfocus_weights_kai_dominant(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.STUCK_IN_HYPERFOCUS_LOOP]
        assert w.kai >= 0.60

    def test_shutdown_weights_myra_dominant(self):
        w = DISTRESS_WEIGHT_MAP[DistressInput.DONT_KNOW_SHUT_DOWN]
        assert w.myra >= 0.75

    def test_all_maps_normalize_to_one(self):
        for distress_input, weights in DISTRESS_WEIGHT_MAP.items():
            total = weights.ash + weights.sol + weights.echo + weights.kai + weights.myra
            assert abs(total - 1.0) < 0.01, f"{distress_input.value} weights don't sum to 1.0 (got {total})"


class TestFusionEngine:
    def setup_method(self):
        self.engine = FusionEngine()
        self.toi = TOIConfig()

    def _make_context(self, distress_input=None, crisis_score=0.0, silent=False):
        return EngineContext(
            distress_input=distress_input,
            crisis_level_score=crisis_score,
            silent_mode_active=silent,
        )

    def test_compute_weights_meltdown(self):
        ctx = self._make_context(DistressInput.EVERYTHING_HURTS_MELTDOWN, crisis_score=0.5)
        weights = self.engine.compute_weights(ctx, self.toi)
        name, weight = weights.dominant_persona()
        assert name in ("ash", "myra")  # One of the two should dominate

    def test_compute_weights_shutdown_triggers_myra(self):
        ctx = self._make_context(DistressInput.DONT_KNOW_SHUT_DOWN, crisis_score=0.6)
        weights = self.engine.compute_weights(ctx, self.toi)
        assert weights.myra >= 0.5  # Myra must heavily dominate shutdown

    def test_compute_weights_normalized(self):
        for di in DistressInput:
            ctx = self._make_context(di, crisis_score=0.3)
            weights = self.engine.compute_weights(ctx, self.toi)
            total = weights.ash + weights.sol + weights.echo + weights.kai + weights.myra
            assert abs(total - 1.0) < 0.01, f"Weights not normalized for {di.value}"

    def test_compute_weights_exclusion(self):
        toi = TOIConfig(excluded_personas=["kai"])
        ctx = self._make_context(DistressInput.STUCK_IN_HYPERFOCUS_LOOP, crisis_score=0.4)
        weights = self.engine.compute_weights(ctx, toi)
        assert weights.kai == 0.0

    def test_compute_weights_preference_boost(self):
        toi_base = TOIConfig()
        toi_preferred = TOIConfig(preferred_personas=["echo"])
        ctx = self._make_context(DistressInput.CANT_STOP_SELF_BLAME, crisis_score=0.3)
        weights_base = self.engine.compute_weights(ctx, toi_base)
        weights_preferred = self.engine.compute_weights(ctx, toi_preferred)
        # Echo should have higher relative weight when preferred
        assert weights_preferred.echo >= weights_base.echo

    def test_high_crisis_boosts_myra(self):
        ctx_low = self._make_context(crisis_score=0.1)
        ctx_high = self._make_context(crisis_score=0.85)
        weights_low = self.engine.compute_weights(ctx_low, self.toi)
        weights_high = self.engine.compute_weights(ctx_high, self.toi)
        assert weights_high.myra >= weights_low.myra

    def test_blend_response_returns_blended_response(self):
        ctx = self._make_context(DistressInput.EVERYTHING_HURTS_MELTDOWN, crisis_score=0.5)
        weights = self.engine.compute_weights(ctx, self.toi)
        blended = self.engine.blend_response(ctx, weights, self.toi)
        assert isinstance(blended, BlendedResponse)
        assert blended.system_prompt
        assert blended.template_response
        assert blended.dominant_persona
        assert blended.active_personas

    def test_blend_response_shutdown_triggers_silent_mode(self):
        ctx = self._make_context(DistressInput.DONT_KNOW_SHUT_DOWN, crisis_score=0.7)
        weights = self.engine.compute_weights(ctx, self.toi)
        blended = self.engine.blend_response(ctx, weights, self.toi)
        assert blended.silent_mode_triggered is True

    def test_infer_distress_from_text_meltdown(self):
        result = self.engine.infer_distress_input_from_text("I'm having a complete meltdown")
        assert result == DistressInput.EVERYTHING_HURTS_MELTDOWN

    def test_infer_distress_from_text_hyperfocus(self):
        result = self.engine.infer_distress_input_from_text("I keep going down a rabbit hole and can't stop")
        assert result == DistressInput.STUCK_IN_HYPERFOCUS_LOOP

    def test_infer_distress_from_text_shutdown(self):
        result = self.engine.infer_distress_input_from_text("I've completely shut down, can't find words")
        assert result == DistressInput.DONT_KNOW_SHUT_DOWN

    def test_system_prompt_contains_persona_names(self):
        ctx = self._make_context(DistressInput.EVERYTHING_HURTS_MELTDOWN, crisis_score=0.5)
        weights = self.engine.compute_weights(ctx, self.toi)
        blended = self.engine.blend_response(ctx, weights, self.toi)
        # The dominant personas (Ash, Myra) should be in the system prompt
        assert "ASH" in blended.system_prompt or "Ash" in blended.system_prompt

    def test_no_task_loop_guard_in_prompt(self):
        toi = TOIConfig(allow_task_loops=False)
        ctx = self._make_context(DistressInput.EVERYTHING_HURTS_MELTDOWN, crisis_score=0.5)
        weights = self.engine.compute_weights(ctx, toi)
        blended = self.engine.blend_response(ctx, weights, toi)
        assert "NO TASK LOOPS" in blended.system_prompt


class TestIndividualPersonas:
    def test_ash_builds_system_prompt(self):
        ash = AshPersona()
        prompt = ash.build_system_prompt(0.45, ToneProfile.SUPPORTIVE_DEFAULT)
        assert "Ash" in prompt or "ash" in prompt.lower()
        assert len(prompt) > 20

    def test_ash_template_response_high_weight(self):
        ash = AshPersona()
        response = ash.get_template_response(0.45)
        assert isinstance(response, str)
        assert len(response) > 5

    def test_myra_silent_mode_response(self):
        myra = MyraPersona()
        response = myra.get_template_response(0.80, silent_mode=True)
        assert isinstance(response, str)
        # Silent mode responses should be very short
        assert len(response.split()) <= 5

    def test_sol_activation_signals(self):
        sol = SolPersona()
        assert sol.matches_activation_signal("I can't start anything today")

    def test_echo_activation_signals(self):
        echo = EchoPersona()
        assert echo.matches_activation_signal("I hate myself for failing again")

    def test_kai_activation_signals(self):
        kai = KaiPersona()
        assert kai.matches_activation_signal("I went down a rabbit hole again")

    def test_myra_activation_signals(self):
        myra = MyraPersona()
        assert myra.matches_activation_signal("I've completely shut down")

    def test_myra_silent_mode_trigger(self):
        myra = MyraPersona()
        assert myra.silent_mode_trigger is True

    def test_ash_silence_compatible(self):
        ash = AshPersona()
        assert ash.silence_compatible is True
