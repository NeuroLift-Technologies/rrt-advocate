# rrt-advocate

Protective-layer RRT AIdvocAIte for the HAIEF Solidarity Framework.

## What changed in v2

This repository now implements:

- TOI/OTOI governance middleware before response generation.
- Dynamic persona fusion across the five OG personas (ASH, SOL, ECHO, KAI, MYRA).
- A local-first 3-layer Crisis Detection Engine (CDE).
- Tiered Activation Dialogue Tree with Stage 1 consent gating and Stage 2 distress mapping.
- Configurable tone profiles (`supportive_default`, `minimal`, `directive`, `therapeutic_reflective`).

## Repository structure

```text
src/
  __init__.py
  rrt_advocate.py      # Main orchestration entrypoint
  models.py            # Shared dataclasses/enums
  toi_otoi.py          # TOI + OTOI policy enforcement
  personas.py          # Persona definitions + fusion algorithm
  dialogue_tree.py     # Stage routing and Stage 2 mapping
  tone_profiles.py     # Prompt tone packaging
  cde.py               # Local-first 3-layer crisis detection

config/
  crisis_thresholds.yaml  # v2 config with TOI/OTOI, CDE, stage mappings

tests/
  test_rrt_advocate.py
```

## Quick usage

```python
from src.rrt_advocate import RRTAdvocate

advocate = RRTAdvocate(
    user_id="demo-user",
    toi_config={
        "tone_profile": "minimal",
        "pacing": "slow",
        "cognitive_scaffolding": "low",
        "safety_boundaries": {
            "require_consent_before_activation": True,
            "disallowed_response_patterns": [],
        },
    },
)

# Stage 1: consent gate
entry = advocate.process_interaction(user_message="I need help", stage=1)
print(entry.prompt_package)

# Stage 2: user distress selection + orchestration
guided = advocate.process_interaction(
    user_message="Everything hurts",
    stage=2,
    consent=True,
    stage_2_input="Everything hurts / Meltdown",
)
print(guided.prompt_package)
```

## Testing

Run:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Design principles

- Local-first and privacy-centric CDE processing.
- Agency-first intervention (explicit consent before activation).
- Anti-gaslight / shame-resistant language defaults.
- No forced productivity in burnout, meltdown, or shutdown flows.
