"""Tests for the Tiered Activation Dialogue Tree and Consent Manager."""
import pytest
from src.dialogue.tiered_tree import TieredDialogueTree, DialogueStage, STAGE2_OPTIONS
from src.dialogue.consent_manager import ConsentManager


class TestConsentManager:
    def setup_method(self):
        self.cm = ConsentManager()

    def test_yes_grants_consent(self):
        state = self.cm.evaluate("yes")
        assert state.consented is True
        assert state.silent_mode_requested is False

    def test_no_denies_consent(self):
        state = self.cm.evaluate("no")
        assert state.consented is False

    def test_silent_sets_silent_mode(self):
        state = self.cm.evaluate("silent")
        assert state.consented is True
        assert state.silent_mode_requested is True

    def test_ambiguous_input_grants_consent(self):
        state = self.cm.evaluate("I suppose so")
        assert state.consented is True

    def test_reset_clears_state(self):
        self.cm.evaluate("yes")
        self.cm.reset()
        assert self.cm.consented is False

    def test_grant_method(self):
        self.cm.grant()
        assert self.cm.consented is True

    def test_revoke_records_stage(self):
        self.cm.grant()
        self.cm.revoke(stage="stage_1")
        assert self.cm.consented is False
        assert "stage_1" in self.cm._state.declined_at


class TestTieredDialogueTree:
    def setup_method(self):
        self.tree = TieredDialogueTree()

    def test_initial_stage_is_ambient(self):
        assert self.tree.current_stage == DialogueStage.AMBIENT

    def test_trigger_entry_moves_to_consent(self):
        result = self.tree.trigger_entry()
        assert result.stage == DialogueStage.CONSENT_CHECKPOINT
        assert len(result.options) >= 2

    def test_consent_yes_moves_to_assessment(self):
        self.tree.trigger_entry()
        result = self.tree.handle_consent("yes")
        assert result.next_stage == DialogueStage.PERSONA_RESPONSE or \
               result.stage == DialogueStage.DISTRESS_ASSESSMENT

    def test_consent_no_returns_to_ambient(self):
        self.tree.trigger_entry()
        result = self.tree.handle_consent("no")
        assert result.next_stage == DialogueStage.AMBIENT

    def test_consent_silent_sets_silent_mode(self):
        self.tree.trigger_entry()
        result = self.tree.handle_consent("silent")
        assert result.silent_mode is True
        assert result.persona_blend is not None
        assert result.persona_blend.lead_persona.name == "MYRA"

    def test_stage2_meltdown_leads_ash_or_myra(self):
        result = self.tree.handle_distress_assessment("meltdown")
        assert result.persona_blend is not None
        assert result.persona_blend.lead_persona.name in ("ASH", "MYRA")

    def test_stage2_task_paralysis_leads_sol(self):
        result = self.tree.handle_distress_assessment("task_paralysis")
        assert result.persona_blend is not None
        assert result.persona_blend.lead_persona.name == "SOL"

    def test_stage2_self_blame_leads_echo(self):
        result = self.tree.handle_distress_assessment("self_blame")
        assert result.persona_blend is not None
        assert result.persona_blend.lead_persona.name == "ECHO"

    def test_stage2_hyperfocus_leads_kai(self):
        result = self.tree.handle_distress_assessment("hyperfocus_loop")
        assert result.persona_blend is not None
        assert result.persona_blend.lead_persona.name == "KAI"

    def test_stage2_shutdown_leads_myra_and_silent(self):
        result = self.tree.handle_distress_assessment("shutdown")
        assert result.persona_blend is not None
        assert result.persona_blend.lead_persona.name == "MYRA"
        assert result.silent_mode is True

    def test_checkin_helpful_moves_toward_closure(self):
        result = self.tree.handle_checkin(helpful=True)
        assert result.next_stage == DialogueStage.CLOSURE

    def test_checkin_not_helpful_returns_to_assessment(self):
        result = self.tree.handle_checkin(helpful=False)
        assert result.next_stage == DialogueStage.DISTRESS_ASSESSMENT

    def test_close_session_message_non_empty(self):
        result = self.tree.close_session()
        assert len(result.message) > 0
        assert result.next_stage == DialogueStage.AMBIENT

    def test_reset_returns_to_ambient(self):
        self.tree.trigger_entry()
        self.tree.reset()
        assert self.tree.current_stage == DialogueStage.AMBIENT

    def test_all_stage2_options_have_valid_ids(self):
        valid_ids = {"meltdown", "task_paralysis", "self_blame", "hyperfocus_loop", "shutdown"}
        for opt in STAGE2_OPTIONS:
            assert opt["id"] in valid_ids

    def test_free_text_input_handled_gracefully(self):
        result = self.tree.handle_distress_assessment("I just feel completely lost and frozen")
        assert result.persona_blend is not None
