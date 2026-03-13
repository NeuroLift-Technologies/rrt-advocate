# RRT AIdvocAIte

**Protective Layer of the Solidarity Framework — NeuroLift Technologies**

---

## Mission

The RRT AIdvocAIte is the crisis-intervention engine of the Human-AI ElevAItion Foundation (HAIEF) **Solidarity Framework**. It replaces the former one-dimensional severity scale with a TOI-compliant, dynamically weighted, multi-persona orchestration engine built on two framework layers:

| Layer | Components |
|---|---|
| **Constitutional** | TOI (Terms of Interaction) · OTOI (Orchestrated TOI) |
| **Protective** | RRT AIdvocAIte · Sleepwalker Protocol |

## Architecture

```
User Message
     │
     ▼
┌────────────────────────────────┐
│  Crisis Detection Engine (CDE) │   ← 3-layer local-first pipeline
│  L1 Keyword · L2 Sentiment ·  │
│  L3 Behavioural                │
└────────────┬───────────────────┘
             │ CrisisAssessment
             ▼
┌────────────────────────────────┐
│  Tiered Dialogue Tree          │   ← Stages 0–5, consent-first
│  Detection → Consent →         │
│  Assessment → Support →        │
│  Grounding → Transition        │
└────────────┬───────────────────┘
             │ DistressInput
             ▼
┌────────────────────────────────┐
│  Persona Fusion Engine         │   ← 5 OGs, dynamic weights 0.0–1.0
│  Ash · Sol · Echo · Kai · Myra │
└────────────┬───────────────────┘
             │ PersonaContributions
             ▼
┌────────────────────────────────┐
│  TOI-OTOI Governance Wrapper   │   ← Enforces user's interaction contract
│  Tone · Pacing · Scaffolding · │
│  Safety Boundaries             │
└────────────┬───────────────────┘
             │
             ▼
        FusedResponse
```

## The Five Original Guides

| Persona | Domain | Trigger |
|---|---|---|
| **ASH** | Burnout validation, shame diffusion | "Everything hurts / Meltdown" |
| **SOL** | Executive function scaffolding | "Can't do basic tasks" |
| **ECHO** | Cognitive reframing, self-talk mirroring | "Can't stop self-blame" |
| **KAI** | Hyperfocus / fixation redirection | "Stuck in hyperfocus/loop" |
| **MYRA** | Relational safety, Silent Mode | "Don't know / Shut down" |

## Tone Profiles

| Profile | Style | Best for |
|---|---|---|
| **Supportive** | Warm, validating | Ash, Myra |
| **Minimal** | Extremely concise | Any (lowest cognitive load) |
| **Directive** | Clear, action-oriented | Sol, Kai |
| **Therapeutic** | Empathetic, soft Socratic | Ash, Echo |

## Dialogue Stages

| Stage | Name | What happens |
|---|---|---|
| 0 | Detection | Passive CDE monitoring — no user interaction |
| 1 | Consent | Entry prompt — system **must** obtain opt-in |
| 2 | Assessment | Low-demand self-report (5 options) |
| 3 | Support | Persona-blended active response |
| 4 | Grounding | De-escalation exercises |
| 5 | Transition | Gentle exit, follow-up scheduling, resource links |

## Quick Start

```bash
pip install -r requirements.txt

# Run tests (90 tests, < 1 s)
python3 -m pytest tests/ -v
```

```python
from src.rrt_advocate import RRTAdvocate

rrt = RRTAdvocate(user_id="user-001")

# Neutral message — stays in Stage 0 (detection)
rrt.process_message("I'm doing fine today.")

# Distress detected — moves to Stage 1 (consent prompt)
rrt.process_message("I can't cope, everything is too much")

# User consents — moves to Stage 2 (assessment options)
rrt.process_message("Yes, I could use some support")

# User selects distress type — Stage 3 (fused persona response)
result = rrt.process_message("Can't do basic tasks")
print(result["message"])  # Sol-weighted scaffolding
```

## Repository Structure

```
src/
├── models.py                     # Shared enums, dataclasses
├── rrt_advocate.py               # Top-level orchestrator
├── toi/                          # TOI-OTOI Governance Wrapper
├── personas/                     # Persona Fusion Engine (5 OGs)
├── dialogue/                     # Tiered Activation Dialogue Tree
├── tone/                         # Configurable Tone Profiles
└── crisis/                       # Crisis Detection Engine (3-layer CDE)

config/
├── crisis_thresholds.yaml        # CDE thresholds & indicator weights
├── toi_defaults.yaml             # Default TOI configuration
├── persona_weights.yaml          # Distress → persona weight map
└── tone_profiles.yaml            # Tone profile reference

tests/                            # 90 tests across 6 modules
```

## Design Principles

- **Local-First**: CDE processes on-device. User data never leaves the machine by default.
- **Anti-Gaslight / Shame-Resistant**: Non-judgmental naming, error handling, and prompts.
- **No Forced Productivity**: Burnout → rest. Never force a task loop.
- **Agency First**: Stage 1 consent is mandatory before any intervention.
- **TOI Compliance**: Every response passes through the Governance Wrapper.

## Crisis Resources

If you are experiencing a mental health crisis:

- **988 Suicide & Crisis Lifeline** — call or text **988**
- **Crisis Text Line** — text **HOME** to **741741**
- **Emergency Services** — **911**
- **CHADD** — chadd.org
- **ADDitude** — additudemag.com

---

**NeuroLift Technologies**
*Tech That Gets You · Nothing About Us Without Us · ElevAIte Your Mind*
