"""Integration tests for the RRT AIdvocAIte orchestrator."""

import pytest
from src.rrt_advocate import RRTAdvocate, CrisisLevel, _score_to_level


class TestScoreToLevel:
    def test_green(self):
        assert _score_to_level(0.0) == CrisisLevel.GREEN
        assert _score_to_level(0.10) == CrisisLevel.GREEN

    def test_yellow(self):
        assert _score_to_level(0.20) == CrisisLevel.YELLOW
        assert _score_to_level(0.30) == CrisisLevel.YELLOW

    def test_orange(self):
        assert _score_to_level(0.40) == CrisisLevel.ORANGE
        assert _score_to_level(0.55) == CrisisLevel.ORANGE

    def test_red(self):
        assert _score_to_level(0.70) == CrisisLevel.RED
        assert _score_to_level(0.80) == CrisisLevel.RED

    def test_black(self):
        assert _score_to_level(0.90) == CrisisLevel.BLACK
        assert _score_to_level(1.0) == CrisisLevel.BLACK


class TestRRTAdvocate:
    def test_creation_with_defaults(self):
        adv = RRTAdvocate("user_001")
        status = adv.get_status()
        assert status["user_id"] == "user_001"
        assert status["crisis_level"] == "stable"
        assert status["interaction_count"] == 0

    def test_creation_with_toi(self):
        toi_dict = {"tone": "minimal", "allowed_personas": ["ash", "myra"]}
        adv = RRTAdvocate("user_002", toi_dict=toi_dict)
        assert adv.session.toi.tone.value == "minimal"
        assert len(adv.session.toi.allowed_personas) == 2

    def test_calm_message_stays_passive(self):
        adv = RRTAdvocate("user_003")
        result = adv.process_message("The weather is nice today")
        assert result["stage"] == "passive_observation"
        assert result["text"] == ""

    def test_distressed_message_triggers_entry(self):
        adv = RRTAdvocate("user_004")
        result = adv.process_message(
            "I'm worthless, I can't do anything, everything hurts, "
            "I'm broken, make it stop"
        )
        assert result["stage"] == "ENTRY_PROMPT"
        assert len(result["text"]) > 0
        assert len(result["options"]) > 0

    def test_consent_then_distress_selection(self):
        adv = RRTAdvocate("user_005")
        adv.process_message(
            "I'm worthless, everything hurts, I'm broken, can't cope"
        )
        result = adv.process_selection("Yes, I'd like support")
        assert result["stage"] == "DISTRESS_ASSESSMENT"

        result = adv.process_selection("Everything hurts / Meltdown")
        assert result["stage"] == "PERSONA_FUSION"
        assert len(result["text"]) > 0

    def test_consent_declined(self):
        adv = RRTAdvocate("user_006")
        adv.process_message(
            "I'm worthless, everything hurts, can't cope, meltdown"
        )
        result = adv.process_selection("Not right now")
        assert result["stage"] == "GRACEFUL_EXIT"

    def test_exit_session(self):
        adv = RRTAdvocate("user_007")
        result = adv.exit_session()
        assert result["stage"] == "GRACEFUL_EXIT"

    def test_update_toi_mid_session(self):
        adv = RRTAdvocate("user_008")
        adv.update_toi({"tone": "directive", "safety_boundaries": ["no_timers"]})
        assert adv.session.toi.tone.value == "directive"

    def test_full_flow_all_distress_types(self):
        for option in [
            "Everything hurts / Meltdown",
            "Can't do basic tasks",
            "Can't stop self-blame",
            "Stuck in hyperfocus/loop",
            "Don't know / Shut down",
        ]:
            adv = RRTAdvocate("user_flow")
            adv.process_message(
                "I'm worthless, everything hurts, can't cope, meltdown"
            )
            adv.process_selection("Yes, I'd like support")
            result = adv.process_selection(option)
            assert result["stage"] == "PERSONA_FUSION"
            if "Shut down" in option:
                assert result["silent_mode"] is True

    def test_interaction_count_increments(self):
        adv = RRTAdvocate("user_count")
        adv.process_message("hello")
        adv.process_message("hello again")
        assert adv.get_status()["interaction_count"] == 2

    def test_cde_summary_included(self):
        adv = RRTAdvocate("user_cde")
        result = adv.process_message("I feel terrible and hopeless")
        assert "cde_summary" in result
        assert "aggregate_distress" in result["cde_summary"]
