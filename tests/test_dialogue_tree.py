"""Tests for the Tiered Activation Dialogue Tree."""

import pytest
from src.toi.toi_config import TOIConfig, TonePreference, SafetyBoundary
from src.dialogue.dialogue_tree import (
    DialogueTree,
    ActivationStage,
    StageInput,
    StageOutput,
    STAGE2_OPTIONS,
)
from src.dialogue.consent_manager import ConsentManager, ConsentState
from src.dialogue.stage_handlers import StageHandlers


class TestConsentManager:
    def test_initial_state_not_asked(self):
        cm = ConsentManager()
        assert cm.state == ConsentState.NOT_ASKED

    def test_request_consent_moves_to_pending(self):
        cm = ConsentManager()
        prompt = cm.request_consent()
        assert cm.state == ConsentState.PENDING
        assert len(prompt) > 0

    def test_grant(self):
        cm = ConsentManager()
        cm.request_consent()
        cm.grant()
        assert cm.is_granted is True

    def test_decline(self):
        cm = ConsentManager()
        cm.request_consent()
        cm.decline()
        assert cm.state == ConsentState.DECLINED

    def test_withdraw(self):
        cm = ConsentManager()
        cm.request_consent()
        cm.grant()
        cm.withdraw()
        assert cm.state == ConsentState.WITHDRAWN

    def test_reset(self):
        cm = ConsentManager()
        cm.request_consent()
        cm.grant()
        cm.reset()
        assert cm.state == ConsentState.NOT_ASKED


class TestStageHandlers:
    def test_meltdown_input_variants(self):
        sh = StageHandlers()
        for variant in ["everything hurts", "Everything hurts / Meltdown", "meltdown"]:
            key = sh.resolve_input(variant)
            assert key == "meltdown"

    def test_cant_do_tasks_variants(self):
        sh = StageHandlers()
        for variant in ["can't do basic tasks", "cant do basic tasks", "cant_do_tasks"]:
            key = sh.resolve_input(variant)
            assert key == "cant_do_tasks"

    def test_self_blame_variants(self):
        sh = StageHandlers()
        key = sh.resolve_input("Can't stop self-blame")
        assert key == "self_blame"

    def test_hyperfocus_variants(self):
        sh = StageHandlers()
        key = sh.resolve_input("Stuck in hyperfocus/loop")
        assert key == "hyperfocus_loop"

    def test_shutdown_variants(self):
        sh = StageHandlers()
        for variant in ["Don't know / Shut down", "shut down", "shutdown"]:
            key = sh.resolve_input(variant)
            assert key == "shutdown"

    def test_unknown_input_defaults_meltdown(self):
        sh = StageHandlers()
        key = sh.resolve_input("something unknown")
        assert key == "meltdown"

    def test_get_weights_returns_persona_weights(self):
        sh = StageHandlers()
        w = sh.get_weights("meltdown")
        assert w.ash > 0.5
        assert w.myra > 0.5

    def test_get_distress_context(self):
        sh = StageHandlers()
        ctx = sh.get_distress_context("shutdown")
        assert ctx["distress_type"] == "shutdown"
        assert ctx["silent_mode"] is True

    def test_meltdown_weights_heavy_ash_myra(self):
        sh = StageHandlers()
        w = sh.get_weights("Everything hurts / Meltdown")
        assert w.ash >= 0.8
        assert w.myra >= 0.7

    def test_cant_do_tasks_weights_heavy_sol(self):
        sh = StageHandlers()
        w = sh.get_weights("Can't do basic tasks")
        assert w.sol >= 0.8

    def test_self_blame_weights_heavy_echo(self):
        sh = StageHandlers()
        w = sh.get_weights("Can't stop self-blame")
        assert w.echo >= 0.8

    def test_hyperfocus_weights_heavy_kai(self):
        sh = StageHandlers()
        w = sh.get_weights("Stuck in hyperfocus/loop")
        assert w.kai >= 0.8

    def test_shutdown_weights_heavy_myra(self):
        sh = StageHandlers()
        w = sh.get_weights("Don't know / Shut down")
        assert w.myra >= 0.9


class TestDialogueTree:
    def test_initial_stage_is_passive(self):
        tree = DialogueTree(TOIConfig())
        assert tree.current_stage == ActivationStage.PASSIVE_OBSERVATION

    def test_trigger_entry_moves_to_stage_1(self):
        tree = DialogueTree(TOIConfig())
        output = tree.trigger_entry()
        assert tree.current_stage == ActivationStage.ENTRY_PROMPT
        assert len(output.text) > 0
        assert len(output.options) == 2

    def test_consent_granted_moves_to_stage_2(self):
        tree = DialogueTree(TOIConfig())
        tree.trigger_entry()
        output = tree.advance(StageInput(
            selected_option="Yes, I'd like support",
            consent_response=True,
        ))
        assert tree.current_stage == ActivationStage.DISTRESS_ASSESSMENT
        assert len(output.options) == 5

    def test_consent_declined_exits(self):
        tree = DialogueTree(TOIConfig())
        tree.trigger_entry()
        output = tree.advance(StageInput(
            selected_option="Not right now",
            consent_response=False,
        ))
        assert tree.current_stage == ActivationStage.GRACEFUL_EXIT

    def test_distress_selection_produces_fused_response(self):
        tree = DialogueTree(TOIConfig())
        tree.trigger_entry()
        tree.advance(StageInput(selected_option="Yes, I'd like support", consent_response=True))
        output = tree.advance(StageInput(selected_option="Everything hurts / Meltdown"))
        assert tree.current_stage == ActivationStage.PERSONA_FUSION
        assert output.fused_response is not None
        assert len(output.text) > 0

    def test_shutdown_selection_activates_silent_mode(self):
        tree = DialogueTree(TOIConfig())
        tree.trigger_entry()
        tree.advance(StageInput(selected_option="Yes, I'd like support", consent_response=True))
        output = tree.advance(StageInput(selected_option="Don't know / Shut down"))
        assert output.silent_mode is True

    def test_try_something_else_loops_back(self):
        tree = DialogueTree(TOIConfig())
        tree.trigger_entry()
        tree.advance(StageInput(selected_option="Yes", consent_response=True))
        tree.advance(StageInput(selected_option="Everything hurts / Meltdown"))
        output = tree.advance(StageInput(selected_option="Try something else"))
        assert tree.current_stage == ActivationStage.ONGOING_SUPPORT
        assert len(output.options) > 0

    def test_exit_returns_to_passive(self):
        tree = DialogueTree(TOIConfig())
        tree.trigger_entry()
        tree.advance(StageInput(selected_option="Yes", consent_response=True))
        output = tree.exit()
        assert tree.current_stage == ActivationStage.GRACEFUL_EXIT
        assert tree.consent.state == ConsentState.WITHDRAWN

    def test_all_five_stage2_options_produce_output(self):
        for option in STAGE2_OPTIONS:
            tree = DialogueTree(TOIConfig())
            tree.trigger_entry()
            tree.advance(StageInput(selected_option="Yes", consent_response=True))
            output = tree.advance(StageInput(selected_option=option))
            assert output.fused_response is not None
