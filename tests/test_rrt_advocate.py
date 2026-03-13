"""Integration tests for the top-level RRTAdvocate orchestrator."""

import asyncio
import pytest

from src.rrt_advocate import RRTAdvocate
from src.models import CrisisLevel, DialogueStage


class TestRRTAdvocateOrchestration:
    """Full end-to-end flow through the Protective Layer."""

    @pytest.fixture()
    def advocate(self):
        return RRTAdvocate(user_id="test-user-001")

    def test_green_stays_in_detection(self, advocate):
        payload = advocate.process_message("I'm feeling fine today, thanks.")
        assert payload["stage"] == 0
        assert payload["assessment"]["level"] == "stable"

    def test_distress_triggers_consent(self, advocate):
        payload = advocate.process_message(
            "I'm worthless, i can't do anything right, everything is too much"
        )
        assert payload["stage"] == 1
        assert payload.get("options")

    def test_full_happy_path(self, advocate):
        advocate.process_message(
            "I'm a failure, i can't cope, i'm drowning, make it stop"
        )
        consent = advocate.process_message("Yes, I could use some support")
        assert consent["stage"] == 2

        support = advocate.process_message("Can't do basic tasks")
        assert support["stage"] == 3
        assert support["message"]

    def test_shutdown_triggers_silent(self, advocate):
        advocate.process_message("i'm worthless, everything is too much")
        advocate.process_message("yes")
        support = advocate.process_message("Don't know / Shut down")
        assert support.get("silent_mode") is True

    def test_meltdown_path(self, advocate):
        advocate.process_message("i can't cope, i'm falling apart")
        advocate.process_message("okay")
        support = advocate.process_message("Everything hurts / Meltdown")
        assert support["stage"] == 3
        assert support["message"]

    def test_consent_declined(self, advocate):
        advocate.process_message("i'm worthless and i can't cope")
        declined = advocate.process_message("not right now")
        assert declined["action"] == "consent_declined"

    def test_status_report(self, advocate):
        advocate.process_message("hello")
        report = advocate.get_status_report()
        assert report["user_id"] == "test-user-001"
        assert report["total_messages"] == 1

    def test_toi_update_at_runtime(self, advocate):
        advocate.update_toi({"tone": "minimal"})
        assert advocate._governance.toi.tone.value == "minimal"

    def test_reset(self, advocate):
        advocate.process_message("i'm worthless, everything is too much")
        advocate.process_message("yes")
        advocate.reset()
        report = advocate.get_status_report()
        assert report["dialogue_stage"] == 0

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, advocate):
        assert await advocate.start_monitoring() is True
        assert await advocate.start_monitoring() is True
        assert await advocate.stop_monitoring() is True

    @pytest.mark.asyncio
    async def test_shutdown(self, advocate):
        await advocate.start_monitoring()
        await advocate.shutdown()
        report = advocate.get_status_report()
        assert report["monitoring_active"] is False
