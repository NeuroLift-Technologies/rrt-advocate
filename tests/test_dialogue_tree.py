"""
Tests for the Tiered Activation Dialogue Tree (Stage 0–5).
"""
import pytest
from toi.toi_models import TOIConfig, ToneProfile
from toi.otoi_middleware import OTOIMiddleware
from personas.fusion_engine import FusionEngine, DistressInput
from dialogue.stages import ActivationStage, STAGE_CONFIGS, StageConfig, StageOption
from dialogue.dialogue_tree import DialogueTree, DialogueState


def make_dialogue_tree(toi_kwargs=None, crisis_score=0.0):
    toi = TOIConfig(**(toi_kwargs or {}))
    otoi = OTOIMiddleware(toi, session_id="test")
    return DialogueTree(toi_config=toi, otoi_middleware=otoi, crisis_level_score=crisis_score)


class TestStageConfigs:
    def test_all_stages_defined(self):
        for stage in ActivationStage:
            assert stage in STAGE_CONFIGS, f"Stage {stage.name} missing from STAGE_CONFIGS"

    def test_stage_1_has_consent_options(self):
        config = STAGE_CONFIGS[ActivationStage.STAGE_1_ENTRY]
        option_keys = [opt.key for opt in config.options]
        assert "yes" in option_keys
        assert "not_now" in option_keys
        assert "silent" in option_keys

    def test_stage_2_has_all_distress_options(self):
        config = STAGE_CONFIGS[ActivationStage.STAGE_2_ASSESSMENT]
        option_keys = [opt.key for opt in config.options]
        assert "meltdown" in option_keys
        assert "cant_task" in option_keys
        assert "self_blame" in option_keys
        assert "hyperfocus" in option_keys
        assert "shutdown" in option_keys

    def test_stage_2_options_map_to_distress_inputs(self):
        config = STAGE_CONFIGS[ActivationStage.STAGE_2_ASSESSMENT]
        for opt in config.options:
            if opt.key != "skip":
                assert "distress_input" in opt.metadata

    def test_shutdown_option_activates_silent_mode(self):
        config = STAGE_CONFIGS[ActivationStage.STAGE_2_ASSESSMENT]
        shutdown_opt = next(o for o in config.options if o.key == "shutdown")
        assert shutdown_opt.metadata.get("activate_silent_mode") is True

    def test_stage_1_yes_grants_consent(self):
        config = STAGE_CONFIGS[ActivationStage.STAGE_1_ENTRY]
        yes_opt = next(o for o in config.options if o.key == "yes")
        assert yes_opt.metadata.get("grants_consent") is True


class TestDialogueState:
    def test_initial_stage_is_passive(self):
        tree = make_dialogue_tree()
        assert tree.state.current_stage == ActivationStage.STAGE_0_PASSIVE

    def test_transition_history_recorded(self):
        from dialogue.dialogue_tree import StageTransition
        from datetime import datetime
        state = DialogueState()
        state.record_transition(
            StageTransition(
                from_stage=ActivationStage.STAGE_0_PASSIVE,
                to_stage=ActivationStage.STAGE_1_ENTRY,
                option_key="check_in",
            )
        )
        assert len(state.transition_history) == 1


class TestDialogueTree:
    def test_no_consent_returns_stage_1_prompt(self):
        tree = make_dialogue_tree()
        response = tree.process_free_text("I'm struggling today")
        # Without consent, should show Stage 1 entry
        assert response["stage"] == ActivationStage.STAGE_1_ENTRY.name

    def test_select_yes_grants_consent(self):
        tree = make_dialogue_tree()
        # Force to Stage 1 manually
        tree.state.current_stage = ActivationStage.STAGE_1_ENTRY
        response = tree.process_option_selection("yes")
        assert tree.otoi.check_consent() is True

    def test_select_yes_advances_to_stage_2(self):
        tree = make_dialogue_tree()
        tree.state.current_stage = ActivationStage.STAGE_1_ENTRY
        response = tree.process_option_selection("yes")
        assert response["stage"] == ActivationStage.STAGE_2_ASSESSMENT.name

    def test_select_not_now_returns_to_passive(self):
        tree = make_dialogue_tree()
        tree.state.current_stage = ActivationStage.STAGE_1_ENTRY
        response = tree.process_option_selection("not_now")
        assert response["stage"] == ActivationStage.STAGE_0_PASSIVE.name

    def test_select_silent_mode_option(self):
        tree = make_dialogue_tree()
        tree.state.current_stage = ActivationStage.STAGE_1_ENTRY
        response = tree.process_option_selection("silent")
        assert tree.state.silent_mode_active is True
        assert tree.otoi.state.silent_mode_active is True

    def test_meltdown_selection_sets_distress_input(self):
        tree = make_dialogue_tree()
        tree.otoi.grant_consent()
        tree.state.current_stage = ActivationStage.STAGE_2_ASSESSMENT
        tree.process_option_selection("meltdown")
        assert tree.state.current_distress_input == DistressInput.EVERYTHING_HURTS_MELTDOWN

    def test_shutdown_selection_activates_silent_mode(self):
        tree = make_dialogue_tree()
        tree.otoi.grant_consent()
        tree.state.current_stage = ActivationStage.STAGE_2_ASSESSMENT
        tree.process_option_selection("shutdown")
        assert tree.state.silent_mode_active is True
        assert tree.state.current_distress_input == DistressInput.DONT_KNOW_SHUT_DOWN

    def test_stage_3_generates_intervention_prompt(self):
        tree = make_dialogue_tree()
        tree.otoi.grant_consent()
        tree.state.current_stage = ActivationStage.STAGE_2_ASSESSMENT
        # Select meltdown → moves to Stage 3
        response = tree.process_option_selection("meltdown")
        assert response["stage"] == ActivationStage.STAGE_3_INTERVENTION.name
        # Should have a non-empty prompt
        assert response.get("prompt") or response.get("response_text")

    def test_stage_3_includes_persona_context(self):
        tree = make_dialogue_tree()
        tree.otoi.grant_consent()
        tree.state.current_stage = ActivationStage.STAGE_2_ASSESSMENT
        response = tree.process_option_selection("meltdown")
        assert "persona_context" in response
        pc = response["persona_context"]
        assert "dominant_persona" in pc
        assert "active_personas" in pc
        assert "weights" in pc

    def test_invalid_option_returns_error(self):
        tree = make_dialogue_tree()
        tree.state.current_stage = ActivationStage.STAGE_1_ENTRY
        response = tree.process_option_selection("invalid_key_xyz")
        assert "error" in response

    def test_free_text_infers_distress_shutdown(self):
        tree = make_dialogue_tree()
        tree.otoi.grant_consent()
        tree.state.current_stage = ActivationStage.STAGE_3_INTERVENTION
        tree.process_free_text("I've completely shut down and can't find words")
        assert tree.state.current_distress_input == DistressInput.DONT_KNOW_SHUT_DOWN

    def test_session_summary_structure(self):
        tree = make_dialogue_tree()
        summary = tree.get_session_summary()
        assert "current_stage" in summary
        assert "consent_given" in summary
        assert "silent_mode_active" in summary
        assert "otoi_summary" in summary

    def test_full_journey_stage_0_to_3(self):
        """Simulate the full Stage 0 → 1 (consent) → 2 (distress) → 3 (intervention) journey."""
        tree = make_dialogue_tree()

        # Stage 0: User is passive
        assert tree.state.current_stage == ActivationStage.STAGE_0_PASSIVE

        # Stage 1: Move to entry, grant consent
        tree.state.current_stage = ActivationStage.STAGE_1_ENTRY
        response = tree.process_option_selection("yes")
        assert response["stage"] == ActivationStage.STAGE_2_ASSESSMENT.name
        assert tree.otoi.check_consent() is True

        # Stage 2: Select "can't do basic tasks" → Sol-heavy
        response = tree.process_option_selection("cant_task")
        assert response["stage"] == ActivationStage.STAGE_3_INTERVENTION.name
        assert tree.state.current_distress_input == DistressInput.CANT_DO_BASIC_TASKS

        # Verify Sol is in the active personas
        pc = response.get("persona_context", {})
        active = pc.get("active_personas", [])
        assert "sol" in active or pc.get("dominant_persona") == "sol"
