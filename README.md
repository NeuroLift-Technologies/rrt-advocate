# RRT AIdvocAIte

**Protective Layer of the Solidarity Framework — NeuroLift Technologies**

## Mission

The RRT AIdvocAIte is the **Protective Layer** of the Human-AI ElevAItion Foundation (HAIEF) Solidarity Framework.  It replaces the former generic Green-to-Black severity system with a **TOI-compliant, dynamically weighted, multi-persona orchestration engine** designed for neurodivergent crisis support.

**"When ADHD overwhelms, the AIdvocAIte responds — on your terms."**

## The Solidarity Framework

The Solidarity Framework is the unified standard for all NeuroLift Technologies agents:

| Layer | Components |
|---|---|
| **Constitutional** | TOI (Terms of Interaction) · OTOI (Orchestrated TOI) |
| **Protective** | **RRT AIdvocAIte** · Sleepwalker Protocol |

## Architecture

```
┌──────────────────────────────────────────────────┐
│                 RRT AIdvocAIte                    │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │         TOI-OTOI Governance Wrapper         │  │
│  │  (Tone · Pacing · Scaffolding · Boundaries) │  │
│  └─────────────────┬──────────────────────────┘  │
│                    │                             │
│  ┌─────────────────▼──────────────────────────┐  │
│  │     Tiered Activation Dialogue Tree         │  │
│  │  Stage 0 → 1 → 2 → 3 → 4 → 5 (exit)      │  │
│  │  (Agency-first consent at every gate)       │  │
│  └─────────────────┬──────────────────────────┘  │
│                    │                             │
│  ┌─────────────────▼──────────────────────────┐  │
│  │         Persona Fusion Engine               │  │
│  │  ASH · SOL · ECHO · KAI · MYRA             │  │
│  │  (Dynamic weights 0.0–1.0 per persona)      │  │
│  └─────────────────┬──────────────────────────┘  │
│                    │                             │
│  ┌─────────────────▼──────────────────────────┐  │
│  │    Crisis Detection Engine (CDE)            │  │
│  │  L1: Keyword/Semantic · L2: Sentiment ·     │  │
│  │  L3: Behavioral Pattern (all local-first)   │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │       Configurable Tone Profiles            │  │
│  │  Supportive · Minimal · Directive ·         │  │
│  │  Therapeutic/Reflective                     │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## The 5 Original Guides (OG Personas)

| Persona | Core Role | Activates When |
|---|---|---|
| **ASH** | Validates burnout, diffuses shame, prioritises *being* over *doing* | Meltdown, burnout |
| **SOL** | Scaffolds executive function, breaks down tasks, manages attention fatigue | Can't do basic tasks |
| **ECHO** | Mirrors internal monologue, reframes cognitive distortions | Self-blame, negative self-talk |
| **KAI** | Redirects hyperfocus and fixation into constructive pathways | Stuck in a loop |
| **MYRA** | Provides relational safety, co-regulation, anchors Silent Mode | Shutdown, don't know |

## Tiered Activation Dialogue (Stages 0–5)

| Stage | Name | Description |
|---|---|---|
| 0 | Passive Observation | CDE running; no user-facing output |
| 1 | Entry Prompt | Consent request — "Would you like support?" |
| 2 | Distress Assessment | User selects flavour of distress |
| 3 | Persona Fusion | System generates blended persona response |
| 4 | Ongoing Support | Iterative loop until user exits |
| 5 | Graceful Exit | System returns to Stage 0 |

## Repository Structure

```
src/
├── rrt_advocate.py          # Main orchestrator
├── toi/                     # TOI-OTOI Governance Wrapper
│   ├── toi_config.py        # TOI data models
│   ├── toi_parser.py        # TOI enforcement middleware
│   └── otoi_coordinator.py  # OTOI persona coordination
├── personas/                # Persona Fusion Engine
│   ├── persona_base.py      # Abstract persona contract
│   ├── ash.py               # Burnout validation
│   ├── sol.py               # Executive function scaffolding
│   ├── echo.py              # Cognitive reframing
│   ├── kai.py               # Hyperfocus redirection
│   ├── myra.py              # Relational safety / Silent Mode
│   └── fusion_engine.py     # Dynamic weighting algorithm
├── dialogue/                # Tiered Activation Dialogue Tree
│   ├── dialogue_tree.py     # Stage state machine
│   ├── stage_handlers.py    # Distress → weight mapping
│   └── consent_manager.py   # Agency-first consent tracking
├── detection/               # Crisis Detection Engine (CDE)
│   ├── cde_pipeline.py      # 3-layer pipeline orchestrator
│   ├── keyword_analyzer.py  # Layer 1: Keyword/Semantic fields
│   ├── sentiment_analyzer.py # Layer 2: Sentiment/Emotional tone
│   └── behavioral_analyzer.py # Layer 3: Behavioral patterns
└── tones/                   # Configurable Tone Profiles
    └── tone_profiles.py     # 4 tone mode definitions

config/
├── crisis_thresholds.yaml   # CDE pipeline configuration
├── toi_defaults.yaml        # Default TOI contract
├── persona_weights.yaml     # Distress-to-persona weight maps
└── tone_profiles.yaml       # Tone profile specifications

tests/
├── test_toi.py              # TOI-OTOI tests
├── test_fusion_engine.py    # Persona & fusion tests
├── test_cde.py              # CDE pipeline tests
├── test_dialogue_tree.py    # Dialogue tree tests
├── test_tone_profiles.py    # Tone profile tests
└── test_rrt_advocate.py     # Integration tests
```

## Core Design Principles

- **Local-First & Privacy-Centric** — The CDE never transmits user data externally.
- **Agency First** — The system pauses and asks for consent before engaging.
- **Anti-Gaslight / Shame-Resistant** — No judgmental framing in code or responses.
- **No Forced Productivity** — Burnout is met with rest, never with task pressure.
- **TOI-Compliant** — Every response passes through the user's interaction contract.

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

```bash
git clone https://github.com/NeuroLift-Technologies/rrt-advocate.git
cd rrt-advocate
pip install -r requirements.txt
```

### Quick Start

```python
from src.rrt_advocate import RRTAdvocate

advocate = RRTAdvocate("user_001", toi_dict={
    "tone": "supportive",
    "safety_boundaries": ["no_productivity_framing"],
})

result = advocate.process_message("I can't do anything right, everything hurts")
# → Triggers Entry Prompt (consent request)

result = advocate.process_selection("Yes, I'd like support")
# → Moves to Distress Assessment

result = advocate.process_selection("Everything hurts / Meltdown")
# → Persona Fusion: Ash + Myra weighted response
```

### Running Tests

```bash
python3 -m pytest tests/ -v
```

## Support & Crisis Resources

If you are experiencing a mental health crisis:
- **US**: National Suicide Prevention Lifeline: **988**
- **Crisis Text Line**: Text HOME to **741741**
- **Emergency Services**: **911**

---

**NeuroLift Technologies**
*Tech That Gets You · Nothing About Us Without Us · ElevAIte Your Mind*
