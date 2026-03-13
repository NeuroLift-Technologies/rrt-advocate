"""Targeted tests for the Solidarity Framework protective-layer refactor."""

from __future__ import annotations

import unittest

from src.protective_layer.models import DialogueStage, DistressSignal, ToneProfile
from src.rrt_advocate import RRTAdvocate


class RRTAdvocateProtectiveLayerTests(unittest.IsolatedAsyncioTestCase):
    """Validate TOI gating, fusion mapping, tone enforcement, and local CDE layers."""

    async def asyncSetUp(self) -> None:
        self.advocate = RRTAdvocate("test-user")

    async def test_stage_one_consent_gate_precedes_support(self) -> None:
        plan = await self.advocate.plan_support(
            message="Everything hurts and I cannot think.",
            consent_granted=False,
            response_latency_seconds=90,
        )

        self.assertEqual(plan.stage, DialogueStage.STAGE_1_CONSENT)
        self.assertIsNone(plan.blend)
        self.assertIn("low-demand", plan.user_message.lower())

    async def test_meltdown_maps_to_ash_and_myra(self) -> None:
        plan = await self.advocate.plan_support(
            message="Everything hurts and I am overwhelmed.",
            consent_granted=True,
            distress_signal="Everything hurts / Meltdown",
            history=["I was trying to push through", "Now it all feels like too much"],
            response_latency_seconds=160,
        )

        self.assertEqual(plan.stage, DialogueStage.STAGE_3_SUPPORT)
        self.assertIsNotNone(plan.blend)
        self.assertIn("ash", plan.blend.dominant_personas[:2])
        self.assertIn("myra", plan.blend.dominant_personas[:2])
        self.assertGreater(plan.blend.weights["ash"], plan.blend.weights["sol"])
        self.assertGreater(plan.blend.weights["myra"], plan.blend.weights["kai"])

    async def test_shutdown_triggers_silent_mode_and_hides_timers(self) -> None:
        plan = await self.advocate.plan_support(
            message="don't know",
            consent_granted=True,
            distress_signal="Don't know / Shut down",
            history=["I was trying to answer", "I am blank"],
            response_latency_seconds=260,
        )

        self.assertIsNotNone(plan.blend)
        self.assertEqual(plan.blend.dominant_personas[0], "myra")
        self.assertTrue(plan.blend.silent_mode)
        self.assertTrue(plan.ui_hints["calm_visuals"])
        self.assertFalse(plan.ui_hints["show_timers"])
        self.assertTrue(plan.ui_hints["minimal_text"])

    async def test_toi_can_block_directive_tone(self) -> None:
        toi_config = {
            "toi": {
                "tone": "directive",
                "safety_boundaries": {
                    "allow_directive_tone": False,
                    "require_stage1_consent": True,
                },
            }
        }
        plan = await self.advocate.plan_support(
            message="I can't do basic tasks.",
            consent_granted=True,
            distress_signal="Can't do basic tasks",
            toi_config=toi_config,
            response_latency_seconds=120,
        )

        self.assertIsNotNone(plan.blend)
        self.assertNotEqual(plan.blend.tone_profile, ToneProfile.DIRECTIVE)
        self.assertIn(plan.blend.tone_profile, {ToneProfile.MINIMAL, ToneProfile.SUPPORTIVE_DEFAULT})

    async def test_local_first_cde_uses_three_layers_and_infers_self_blame(self) -> None:
        detection = self.advocate.detector.analyze(
            message="I'm a failure. It is my fault and I hate myself.",
            history=["I was okay earlier today", "This is getting worse"],
            response_latency_seconds=210,
        )

        self.assertEqual(
            [layer.layer_name for layer in detection.layer_scores],
            ["semantic", "sentiment", "behavioral"],
        )
        self.assertTrue(detection.local_only)
        self.assertEqual(detection.dominant_distress, DistressSignal.SELF_BLAME)
        self.assertGreaterEqual(detection.overall_score, 0.45)


if __name__ == "__main__":
    unittest.main()
