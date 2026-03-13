#!/usr/bin/env python3
"""
Run RRT Advocate with Solidarity Framework integration.
Ensure PYTHONPATH includes the src directory.
"""
import sys
from pathlib import Path

# Add src to path for package resolution
src = Path(__file__).resolve().parent / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

# Change to project root for config paths
import os
os.chdir(Path(__file__).resolve().parent)

if __name__ == "__main__":
    import asyncio
    from rrt_advocate import create_rrt_advocate, RRTAdvocate

    async def main():
        print("RRT Advocate - Solidarity Framework Protective Layer")
        print("=" * 55)
        advocate = await create_rrt_advocate("test_user_001")
        assert isinstance(advocate, RRTAdvocate)

        # Solidarity Framework API demo
        print("\n[Stage 1] Consent prompt:", advocate.get_stage_1_consent_prompt())
        print("\n[Stage 2] Options:", advocate.get_stage_2_options())
        blend = advocate.process_stage_2_input("Everything hurts / Meltdown")
        print("\n[Fusion] Blend for 'Everything hurts / Meltdown':", blend)
        print("\n[Tone] Instructions:", advocate.get_tone_instructions()[:80] + "...")

        cde_result = advocate.detect_crisis_from_text("I can't do anything. Everything hurts.")
        if cde_result:
            print("\n[CDE] Detection result:", cde_result)

        print("\nRRT Advocate ready.")
        await advocate.shutdown()

    asyncio.run(main())
