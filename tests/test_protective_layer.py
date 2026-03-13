import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rrt_advocate import RRTAdvocate  # noqa: E402


class TestProtectiveLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.config_path = str(ROOT / "config" / "crisis_thresholds.yaml")
        self.default_toi = {
            "tone_profile": "supportive_default",
            "pacing": "steady",
            "cognitive_scaffolding": "moderate",
            "safety_boundaries": ["No shaming language"],
            "allowed_personas": ["ash", "sol", "echo", "kai", "myra"],
            "max_personas_per_turn": 2,
        }

    def _activated_advocate(self, toi_overrides=None) -> RRTAdvocate:
        advocate = RRTAdvocate("test-user", self.config_path)
        toi = dict(self.default_toi)
        if toi_overrides:
            toi.update(toi_overrides)
        advocate.ingest_toi(toi)
        advocate.handle_stage1_consent(True)
        return advocate

    def test_requires_toi_before_support(self):
        advocate = RRTAdvocate("test-user", self.config_path)
        result = advocate.process_interaction("help")
        self.assertEqual(result["next_action"], "provide_toi")
        self.assertEqual(result["stage"], 1)

    def test_meltdown_weights_prioritize_ash_and_myra(self):
        advocate = self._activated_advocate()
        result = advocate.handle_stage2_distress(
            distress_input="everything hurts / meltdown",
            user_message="Everything hurts. I am flooded.",
            response_latency_seconds=10,
        )
        sorted_weights = sorted(
            result["persona_weights"].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        top_two = {sorted_weights[0][0], sorted_weights[1][0]}
        self.assertSetEqual(top_two, {"ash", "myra"})
        self.assertFalse(result["silent_mode"])

    def test_shutdown_triggers_silent_mode(self):
        advocate = self._activated_advocate()
        result = advocate.handle_stage2_distress(
            distress_input="don't know / shut down",
            user_message="I don't know. I'm shut down.",
            response_latency_seconds=20,
        )
        self.assertTrue(result["silent_mode"])
        self.assertTrue(result["ui_hints"]["calm_visuals"])
        self.assertFalse(result["ui_hints"]["show_timers"])

    def test_minimal_tone_is_concise(self):
        advocate = self._activated_advocate({"tone_profile": "minimal"})
        result = advocate.handle_stage2_distress(
            distress_input="can't do basic tasks",
            user_message="I can't do even basic tasks",
            response_latency_seconds=5,
        )
        # Minimal profile uses one compact line.
        self.assertLessEqual(len(result["message"]), 120)

    def test_cde_three_layers_raise_risk_on_distress_signals(self):
        advocate = self._activated_advocate()
        advocate.message_history.extend(
            [
                "I'm okay I guess",
                "Now I feel hopeless and worthless",
                "hopeless hopeless hopeless",
            ]
        )
        result = advocate.handle_stage2_distress(
            distress_input="can't stop self-blame",
            user_message="It's all my fault and I feel broken",
            response_latency_seconds=120,
        )
        self.assertGreater(result["cde_overall_risk"], 0.5)
        self.assertTrue(result["cde_flags"])

    def test_otoi_respects_allowed_personas(self):
        advocate = self._activated_advocate(
            {
                "allowed_personas": ["sol"],
                "max_personas_per_turn": 1,
            }
        )
        result = advocate.handle_stage2_distress(
            distress_input="everything hurts / meltdown",
            user_message="everything hurts",
            response_latency_seconds=10,
        )
        self.assertEqual(result["selected_personas"], ["sol"])


if __name__ == "__main__":
    unittest.main()
