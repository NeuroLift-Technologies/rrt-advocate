"""Tests for the Tiered Activation Dialogue Tree."""

import pytest

from src.dialogue.dialogue_tree import DialogueTree
from src.dialogue.stages import StageDefinitions, STAGE_2_OPTION_MAP
from src.models import CrisisAssessment, CrisisLevel, DialogueStage, DistressInput
from src.personas.fusion_engine import FusionEngine
from src.toi.governance import GovernanceMiddleware

from datetime import datetime


def _make_assessment(level=CrisisLevel.YELLOW, confidence=0.5):
    return CrisisAssessment(
        timestamp=datetime.now(),
        crisis_level=level,
        primary_indicators=["test"],
        secondary_indicators=[],
        confidence_score=confidence,
        estimated_duration=None,
        recommended_interventions=[],
        escalation_threshold=0.8,
        user_safety_score=0.7,
    )


@pytest.fixture()
def tree():
    gm = GovernanceMiddleware()
    fe = FusionEngine(gm)
    return DialogueTree(fe)


class TestStageDefinitions:
    def test_all_stages_present(self):
        for stage in DialogueStage:
            spec = StageDefinitions.get(stage)
            assert spec.stage == stage

    def test_stage_2_option_map(self):
        assert StageDefinitions.stage_2_distress("Everything hurts / Meltdown") == DistressInput.MELTDOWN
        assert StageDefinitions.stage_2_distress("Can't do basic tasks") == DistressInput.TASK_PARALYSIS
        assert StageDefinitions.stage_2_distress("Can't stop self-blame") == DistressInput.SELF_BLAME
        assert StageDefinitions.stage_2_distress("Stuck in hyperfocus/loop") == DistressInput.HYPERFOCUS_LOOP
        assert StageDefinitions.stage_2_distress("Don't know / Shut down") == DistressInput.SHUTDOWN

    def test_fuzzy_matching(self):
        assert StageDefinitions.stage_2_distress("meltdown") == DistressInput.MELTDOWN
        assert StageDefinitions.stage_2_distress("basic tasks") == DistressInput.TASK_PARALYSIS

    def test_unknown_defaults_to_shutdown(self):
        assert StageDefinitions.stage_2_distress("xyz") == DistressInput.SHUTDOWN


class TestDialogueTree:
    def test_initial_stage(self, tree):
        assert tree.current_stage == DialogueStage.STAGE_0_DETECTION

    def test_trigger_from_cde_moves_to_consent(self, tree):
        payload = tree.trigger_from_cde(_make_assessment())
        assert tree.current_stage == DialogueStage.STAGE_1_CONSENT
        assert payload["stage"] == 1
        assert payload["options"]

    def test_consent_yes(self, tree):
        tree.trigger_from_cde(_make_assessment())
        payload = tree.respond("Yes, I could use some support")
        assert tree.current_stage == DialogueStage.STAGE_2_ASSESSMENT
        assert payload["stage"] == 2

    def test_consent_no(self, tree):
        tree.trigger_from_cde(_make_assessment())
        payload = tree.respond("Not right now")
        assert payload["action"] == "consent_declined"
        assert "okay" in payload["message"].lower() or "completely" in payload["message"].lower()

    def test_assessment_meltdown(self, tree):
        tree.trigger_from_cde(_make_assessment())
        tree.respond("yes")
        payload = tree.respond("Everything hurts / Meltdown")
        assert tree.current_stage == DialogueStage.STAGE_3_SUPPORT
        assert payload["message"]
        assert payload.get("silent_mode") is False

    def test_assessment_shutdown_triggers_silent(self, tree):
        tree.trigger_from_cde(_make_assessment())
        tree.respond("yes")
        payload = tree.respond("Don't know / Shut down")
        assert payload.get("silent_mode") is True

    def test_advance_through_grounding_and_transition(self, tree):
        tree.trigger_from_cde(_make_assessment())
        tree.respond("yes")
        tree.respond("Can't do basic tasks")
        grounding = tree.advance()
        assert grounding["stage"] == 4
        transition = tree.advance()
        assert transition["stage"] == 5

    def test_transition_check_later(self, tree):
        tree.trigger_from_cde(_make_assessment())
        tree.respond("yes")
        tree.respond("Meltdown")
        tree.advance()
        tree.advance()
        payload = tree.respond("Check in later")
        assert payload["action"] == "schedule_followup"

    def test_transition_resources(self, tree):
        tree.trigger_from_cde(_make_assessment())
        tree.respond("yes")
        tree.respond("Meltdown")
        tree.advance()
        tree.advance()
        payload = tree.respond("Show me some resources")
        assert "988" in payload["message"]

    def test_reset(self, tree):
        tree.trigger_from_cde(_make_assessment())
        tree.respond("yes")
        tree.reset()
        assert tree.current_stage == DialogueStage.STAGE_0_DETECTION
        assert tree.consent_given is False
