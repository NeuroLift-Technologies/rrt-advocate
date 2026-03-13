# RRT Advocate

**Rapid Response Team Advocate - Protective Layer for the Solidarity Framework**

## Mission

`rrt-advocate` now implements the Protective Layer of the Human-AI ElevAItion Foundation (HAIEF) Solidarity Framework. The repository focuses on low-demand, shame-resistant, privacy-centric crisis support for neurodivergent distress.

## What Changed

The repository no longer treats support as a one-dimensional green-to-black severity responder. The new architecture is driven by:

- **TOI middleware**: every interaction is filtered through Terms of Interaction before support is generated.
- **OTOI orchestration**: persona coordination is constrained so no single guide overrides the user's contract.
- **Persona fusion**: Ash, Sol, Echo, Kai, and Myra are blended with dynamic weights.
- **Local-first CDE**: a three-layer pipeline scores semantic distress, sentiment shifts, and behavioral patterns without cloud dependency.
- **Tiered activation tree**: Stage 1 consent and Stage 2 signal selection preserve user agency before the advocate goes active.

## Current Repository Structure

```text
src/
├── __init__.py
├── rrt_advocate.py             # Public façade and async entrypoints
└── protective_layer/
    ├── __init__.py
    ├── engines.py             # TOI parser, CDE, fusion engine, dialogue tree
    └── models.py              # Shared enums and dataclasses

config/
├── crisis_thresholds.yaml     # Protective-layer runtime config
└── toi_defaults.yaml          # Default TOI contract

tests/
└── test_rrt_advocate.py       # Focused protective-layer validation
```

## Protective-Layer Architecture

### 1. TOI-OTOI Governance Wrapper

The advocate reads a TOI contract that controls:

- tone profile
- pacing
- cognitive scaffolding depth
- persona preferences / exclusions
- silent-mode behavior
- safety boundaries such as consent gating and escalation limits

The OTOI governor then enforces that contract over any candidate response plan.

### 2. Persona Fusion Engine

The five OG personas are modeled as weighted contributors:

- **Ash**: validates burnout and diffuses shame
- **Sol**: scaffolds executive function
- **Echo**: mirrors internal monologue and reframes distortions
- **Kai**: redirects loops and hyperfocus
- **Myra**: anchors relational safety and Silent Mode

Stage-2 user signals map directly to base weights, then the CDE can further adjust the blend.

### 3. Local-First Crisis Detection Engine

The CDE now runs in three local layers:

1. **Keyword / semantic field analysis**
2. **Sentiment and emotional tone analysis**
3. **Behavioral pattern analysis**

The result is scored into support-intensity bands while keeping user text local.

### 4. Tiered Activation Dialogue Tree

- **Stage 0**: idle / gentle check-in
- **Stage 1**: consent prompt
- **Stage 2**: distress flavor selection
- **Stage 3**: fused support response
- **Stage 4**: stabilization follow-up
- **Stage 5**: consent-based escalation

## Tone Profiles

The advocate supports four tone profiles:

- `supportive_default`
- `minimal`
- `directive`
- `therapeutic_reflective`

These are configured in `config/crisis_thresholds.yaml` and filtered by TOI safety boundaries before use.

## Quick Start

```python
import asyncio

from src.rrt_advocate import RRTAdvocate


async def demo():
    advocate = RRTAdvocate("demo-user")

    plan = await advocate.plan_support(
        message="Everything hurts and I can't think straight.",
        consent_granted=True,
        distress_signal="Everything hurts / Meltdown",
        history=["I was trying to work", "Now everything feels like too much"],
        response_latency_seconds=180,
    )

    print(plan.to_dict())


asyncio.run(demo())
```

## Development Principles

- **Local-first and privacy-centric**
- **Agency first**
- **Anti-gaslight / shame-resistant**
- **No forced productivity**
- **Consent before escalation**

## Support & Crisis Resources

If a real person is in immediate danger or cannot stay safe:

- **US / Canada**: `988`
- **Emergency services**: local emergency number
- **Crisis Text Line**: Text `HOME` to `741741`
