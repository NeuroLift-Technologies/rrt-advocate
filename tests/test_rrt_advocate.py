"""Integration tests for the full RRT AIdvocAIte pipeline."""
import pytest
from src.rrt_advocate import create_rrt_advocate, RRTAdvocate
from src.dialogue.tiered_tree import DialogueStage


class TestRRTAdvocateIntegration:
    def setup_method(self):
        self.advocate = create_rrt_advocate("test_user")

    def test_green_message_stays_ambient(self):
        result = self.advocate.process_message("Today is going pretty well.")
        assert result["stage"] == "AMBIENT"
        assert result.get("silent_mode", False) is False

    def test_distress_message_triggers_consent(self):
        self.advocate.reset_session()
        result = self.advocate.process_message(
            "I can't stop blaming myself, I'm worthless."
        )
        assert result["stage"] == "CONSENT_CHECKPOINT"
        assert len(result.get("options", [])) >= 2

    def test_consent_yes_leads_to_assessment(self):
        self.advocate.reset_session()
        self.advocate.process_message("I'm completely overwhelmed and can't cope.")
        consent_result = self.advocate.handle_dialogue_input(
            DialogueStage.CONSENT_CHECKPOINT, "yes"
        )
        assert consent_result["stage"] == "DISTRESS_ASSESSMENT"

    def test_full_pipeline_meltdown(self):
        """End-to-end: distress → consent → Stage 2 → persona response."""
        self.advocate.reset_session()
        self.advocate.process_message("Everything hurts, I'm having a meltdown.")
        self.advocate.handle_dialogue_input(DialogueStage.CONSENT_CHECKPOINT, "yes")
        response = self.advocate.handle_dialogue_input(
            DialogueStage.DISTRESS_ASSESSMENT, "meltdown"
        )
        assert "blend" in response
        assert response["blend"]["lead"] in ("ASH", "MYRA")

    def test_full_pipeline_task_paralysis(self):
        self.advocate.reset_session()
        self.advocate.process_message("I'm stuck and can't do anything at all.")
        self.advocate.handle_dialogue_input(DialogueStage.CONSENT_CHECKPOINT, "yes")
        response = self.advocate.handle_dialogue_input(
            DialogueStage.DISTRESS_ASSESSMENT, "task_paralysis"
        )
        assert response["blend"]["lead"] == "SOL"

    def test_full_pipeline_shutdown_silent_mode(self):
        self.advocate.reset_session()
        self.advocate.process_message("I've completely shut down, frozen.")
        self.advocate.handle_dialogue_input(DialogueStage.CONSENT_CHECKPOINT, "yes")
        response = self.advocate.handle_dialogue_input(
            DialogueStage.DISTRESS_ASSESSMENT, "shutdown"
        )
        assert response.get("silent_mode") is True
        assert response["blend"]["lead"] == "MYRA"

    def test_consent_no_stays_ambient(self):
        self.advocate.reset_session()
        self.advocate.process_message("I'm a bit overwhelmed.")
        result = self.advocate.handle_dialogue_input(
            DialogueStage.CONSENT_CHECKPOINT, "no"
        )
        assert result["next_stage"] == "AMBIENT"

    def test_silent_mode_consent_gives_empty_message(self):
        self.advocate.reset_session()
        self.advocate.process_message("I'm overwhelmed.")
        result = self.advocate.handle_dialogue_input(
            DialogueStage.CONSENT_CHECKPOINT, "silent"
        )
        assert result.get("silent_mode") is True
        assert result.get("message") == ""

    def test_get_status_returns_expected_keys(self):
        status = self.advocate.get_status()
        assert "user_id" in status
        assert "dialogue_stage" in status
        assert "consent_granted" in status
        assert "last_detection" in status
        assert "last_blend" in status

    def test_detection_included_in_distress_response(self):
        self.advocate.reset_session()
        result = self.advocate.process_message("I can't stop the self-blame loop.")
        if result["stage"] != "AMBIENT":
            assert "detection" in result

    def test_reset_session_clears_consent(self):
        self.advocate.handle_dialogue_input(DialogueStage.CONSENT_CHECKPOINT, "yes")
        self.advocate.reset_session()
        assert self.advocate._consent.consented is False

    def test_create_factory_returns_rrt_advocate(self):
        advocate = create_rrt_advocate("factory_test")
        assert isinstance(advocate, RRTAdvocate)

    def test_no_productivity_pressure_in_response(self):
        """Burnout input must never trigger a 'push through / complete the task' response."""
        self.advocate.reset_session()
        self.advocate.process_message("Everything hurts, meltdown.")
        self.advocate.handle_dialogue_input(DialogueStage.CONSENT_CHECKPOINT, "yes")
        response = self.advocate.handle_dialogue_input(
            DialogueStage.DISTRESS_ASSESSMENT, "meltdown"
        )
        msg = response.get("message", "")
        pressure_phrases = ["push through", "get it done", "finish the task"]
        for phrase in pressure_phrases:
            assert phrase.lower() not in msg.lower(), f"Productivity pressure phrase found: {phrase!r}"
