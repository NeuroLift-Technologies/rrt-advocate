"""
Tiered activation dialogue tree for low-demand crisis onboarding.
"""

from __future__ import annotations

from .models import DistressSignal, StageDirective


class TieredActivationDialogueTree:
    """Routes Stage 0-5 activation with agency-first consent controls."""

    def stage_1_entry_prompt(self) -> str:
        return (
            "I can activate your RRT support mode now. "
            "Would you like me to do that? (yes/no)"
        )

    def route(
        self,
        *,
        stage: int,
        consent_granted: bool,
        stage_2_input: str | None,
    ) -> StageDirective:
        if stage <= 1 and not consent_granted:
            return StageDirective(
                stage=1,
                needs_consent=True,
                distress_signal=DistressSignal.UNSPECIFIED,
                prompt=self.stage_1_entry_prompt(),
            )

        if stage <= 2:
            return StageDirective(
                stage=2,
                needs_consent=False,
                distress_signal=self.map_stage_2_input(stage_2_input or ""),
            )

        # Stages 3-5 continue with whichever distress profile is active.
        return StageDirective(
            stage=max(3, stage),
            needs_consent=False,
            distress_signal=self.map_stage_2_input(stage_2_input or ""),
        )

    def map_stage_2_input(self, text: str) -> DistressSignal:
        normalized = text.lower().strip()
        if any(token in normalized for token in ["meltdown", "everything hurts", "everything is too much"]):
            return DistressSignal.MELTDOWN
        if any(token in normalized for token in ["can't do basic tasks", "cant do basic tasks", "can't start"]):
            return DistressSignal.TASKS_IMPOSSIBLE
        if any(token in normalized for token in ["self-blame", "self blame", "my fault", "i'm broken", "im broken"]):
            return DistressSignal.SELF_BLAME_LOOP
        if any(token in normalized for token in ["hyperfocus", "loop", "can't stop", "cant stop"]):
            return DistressSignal.HYPERFOCUS_LOOP
        if any(token in normalized for token in ["don't know", "dont know", "shut down", "shutdown", "blank"]):
            return DistressSignal.SHUTDOWN
        return DistressSignal.UNSPECIFIED
