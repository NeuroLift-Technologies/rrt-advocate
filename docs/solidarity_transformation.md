# Solidarity Framework Transformation Notes

This repository has been refactored from a legacy 1D severity responder into a protective-layer orchestration engine aligned with the HAIEF Solidarity Framework.

## Deprecated

- Legacy Green/Yellow/Orange/Red/Black-only routing as the primary decision system.
- Direct intervention dispatch without TOI-mediated consent gating.

## Implemented

1. **TOI/OTOI Governance Wrapper**
   - Enforces Stage 1 consent before full activation.
   - Applies OTOI persona weighting caps so no single persona overrides contract.

2. **Persona Fusion Engine**
   - Dynamic blend across ASH, SOL, ECHO, KAI, MYRA.
   - Stage 2 distress signals map to weighted persona blends.
   - CDE distress tags nudge persona weights.

3. **Tiered Activation Dialogue Tree**
   - Stage 1: consent prompt.
   - Stage 2: distress flavor mapping:
     - "Everything hurts / Meltdown" -> ASH + MYRA dominant.
     - "Can't do basic tasks" -> SOL dominant.
     - "Can't stop self-blame" -> ECHO dominant.
     - "Stuck in hyperfocus/loop" -> KAI dominant.
     - "Don't know / Shut down" -> MYRA dominant + Silent Mode.

4. **Tone Profiles**
   - supportive_default
   - minimal
   - directive
   - therapeutic_reflective

5. **Crisis Detection Engine (Local-First)**
   - Layer 1: keyword/semantic fields.
   - Layer 2: sentiment and polarity drop.
   - Layer 3: behavioral patterns (latency, complexity, looping).

## New file map

- `src/rrt_advocate.py` - orchestration entrypoint
- `src/models.py` - shared dataclasses/enums
- `src/toi_otoi.py` - TOI/OTOI enforcement
- `src/personas.py` - persona fusion
- `src/dialogue_tree.py` - tiered activation logic
- `src/tone_profiles.py` - tone-profile prompt rendering
- `src/cde.py` - local-first CDE pipeline
- `config/crisis_thresholds.yaml` - v2 configuration
- `tests/test_rrt_advocate.py` - architecture validation tests
