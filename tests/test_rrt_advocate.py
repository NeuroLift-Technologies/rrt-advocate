import unittest

from src.cde import LocalFirstCrisisDetectionEngine
from src.models import DistressSignal, OTOIPolicy
from src.rrt_advocate import RRTAdvocate


class TestRRTAdvocateArchitecture(unittest.TestCase):
    def test_stage_1_consent_gate_blocks_activation(self) -> None:
        advocate = RRTAdvocate(user_id="user-1")
        result = advocate.process_interaction(
            user_message="I feel overwhelmed",
            stage=1,
            consent=None,
        )
        self.assertTrue(result.consent_required)
        self.assertFalse(result.consent_granted)
        self.assertIn("Would you like me", result.prompt_package)

    def test_stage_2_meltdown_maps_to_ash_myra_dominant_blend(self) -> None:
        advocate = RRTAdvocate(user_id="user-2")
        result = advocate.process_interaction(
            user_message="Everything hurts and I am melting down",
            stage=2,
            consent=True,
            stage_2_input="Everything hurts / Meltdown",
        )
        self.assertEqual(result.distress_signal, DistressSignal.MELTDOWN)
        self.assertGreaterEqual(result.fusion.persona_weights["ASH"], 0.35)
        self.assertGreaterEqual(result.fusion.persona_weights["MYRA"], 0.35)

    def test_shutdown_enables_silent_mode(self) -> None:
        advocate = RRTAdvocate(
            user_id="user-3",
            toi_config={"tone_profile": "minimal"},
        )
        result = advocate.process_interaction(
            user_message="I don't know. I shut down.",
            stage=2,
            consent=True,
            stage_2_input="Don't know / Shut down",
        )
        self.assertEqual(result.distress_signal, DistressSignal.SHUTDOWN)
        self.assertTrue(result.fusion.silent_mode)
        self.assertIn("Silent Mode: enabled", result.prompt_package)
        self.assertIn("no timers", result.prompt_package.lower())

    def test_otoi_contract_caps_single_persona_weight(self) -> None:
        advocate = RRTAdvocate(
            user_id="user-4",
            otoi_policy=OTOIPolicy(max_persona_weight=0.6, min_active_personas=2),
        )
        result = advocate.process_interaction(
            user_message="I cannot do any task and can't start",
            stage=2,
            consent=True,
            stage_2_input="Can't do basic tasks",
        )
        self.assertLessEqual(max(result.fusion.persona_weights.values()), 0.6)


class TestLocalFirstCDE(unittest.TestCase):
    def test_cde_detects_keywords_sentiment_and_behavior(self) -> None:
        cde = LocalFirstCrisisDetectionEngine()
        result = cde.assess(
            message="I hate myself, I am broken, I can't start anything and I'm stuck",
            recent_messages=[
                "I can't start anything",
                "I can't start anything",
                "I can't start anything",
            ],
            response_latency_seconds=45,
        )
        self.assertGreater(result.layer_1_keywords.score, 0.3)
        self.assertGreater(result.layer_2_sentiment.score, 0.1)
        self.assertGreater(result.layer_3_behavior.score, 0.1)
        self.assertIn("negative_self_talk", result.distress_tags)
        self.assertIn("task_avoidance", result.distress_tags)


if __name__ == "__main__":
    unittest.main()
