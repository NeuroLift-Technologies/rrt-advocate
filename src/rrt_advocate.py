"""Public RRT Advocate entry point."""

from __future__ import annotations

import asyncio
import json

from rrt_core import (
    ActivationStage,
    CrisisAssessment,
    DistressInput,
    RRTAdvocate,
    SafetyBoundaries,
    StageResponse,
    TOIConfig,
    ToneProfile,
    create_rrt_advocate,
)


async def main() -> None:
    advocate = await create_rrt_advocate("demo-user")
    entry = advocate.create_entry_prompt({"tone": "supportive_default"})
    response = advocate.assess_interaction(
        user_message="Everything hurts and I cannot slow my thoughts down.",
        distress_input=DistressInput.EVERYTHING_HURTS_MELTDOWN,
        toi_config={"tone": "supportive_default", "pacing": "gentle"},
        recent_user_messages=["I am overloaded", "too much all at once"],
        response_latency_seconds=95,
        consent_granted=True,
    )
    print("Stage 1:")
    print(entry.message)
    print("
Stage 3:")
    print(
        json.dumps(
            {
                "stage": int(response.stage),
                "message": response.message,
                "active_personas": response.active_personas,
                "persona_weights": response.persona_weights,
                "silent_mode": response.silent_mode,
                "recommended_actions": response.recommended_actions,
                "assessment": response.metadata["assessment"],
            },
            indent=2,
        )
    )


__all__ = [
    "ActivationStage",
    "CrisisAssessment",
    "DistressInput",
    "RRTAdvocate",
    "SafetyBoundaries",
    "StageResponse",
    "TOIConfig",
    "ToneProfile",
    "create_rrt_advocate",
]


if __name__ == "__main__":
    asyncio.run(main())
