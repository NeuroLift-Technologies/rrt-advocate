# RRT Advocate – Handoff Architecture & File Structure

**From:** Gemini (Strategic Planning)  
**To:** Cursor (Implementation)  
**Date:** March 13, 2026  
**Status:** Implementation Complete – Acknowledgment & Proposal

---

## 1. Acknowledgment of Handoff

Cursor confirms receipt and understanding of the Solidarity Framework integration for the RRT AIdvocAIte as the Protective Layer. The following architectural components have been implemented:

- **TOI-OTOI Governance Wrapper**: Middleware that ingests and enforces user's Terms of Interaction before any crisis response
- **Persona Fusion Engine**: Dynamic blending of Ash, Sol, Echo, Kai, Myra based on distress flavor (not raw severity)
- **Tiered Activation Dialogue Tree**: Backend handlers for Stages 0–5, with Stage 1 consent gate and Stage 2→Fusion mapping
- **Configurable Tone Profiles**: Supportive Default, Minimal, Directive, Therapeutic/Reflective
- **Crisis Detection Engine (CDE)**: 3-layer local-first pipeline (Keyword/Semantic, Sentiment, Behavioral)

---

## 2. Proposed & Implemented File Structure

```
rrt-advocate/
├── config/
│   ├── crisis_thresholds.yaml      # Existing – retain for legacy/severity fallback
│   ├── toi_schema.yaml             # NEW: TOI configuration schema
│   ├── persona_weights.yaml        # NEW: Distress input → persona weight mappings
│   └── tone_profiles.yaml         # NEW: Tone profile instructions for LLM prompts
│
├── src/
│   ├── rrt_advocate.py             # REFACTORED: Integrates new components
│   │
│   ├── governance/                 # NEW: TOI-OTOI layer
│   │   ├── __init__.py
│   │   ├── toi_parser.py           # TOI parser, TOIConfig, validation
│   │   └── otoi_coordinator.py     # OTOI coordinator, PersonaBlend application
│   │
│   ├── persona/                    # NEW: Fusion Engine
│   │   ├── __init__.py
│   │   └── fusion_engine.py        # 5-OG weighting, Stage 2 input mapping
│   │
│   ├── dialogue/                   # NEW: Tiered Activation
│   │   ├── __init__.py
│   │   └── stage_handlers.py       # Stage 1 consent, Stage 2→Fusion handlers
│   │
│   ├── prompts/                    # NEW: Tone Profiles
│   │   ├── __init__.py
│   │   └── tone_profiles.py        # ToneProfileLoader, prompt instructions
│   │
│   └── crisis/                     # REFACTORED: 3-layer CDE
│       ├── __init__.py
│       └── detection/
│           ├── __init__.py
│           └── cde.py              # Layer 1 (keyword/semantic), 2 (sentiment), 3 (behavioral)
│
├── docs/
│   ├── integration_guide.md       # Existing
│   └── HANDOFF_ARCHITECTURE.md    # NEW: This document
│
└── (legacy modules: crisis/detectors, crisis/assessors, response/, coordination/, learning/)
    # These were referenced but not present. New architecture replaces them
    # with governance, persona, dialogue, prompts, crisis/detection.
```

---

## 3. Deprecation / Retain Decisions

| Component | Decision |
|-----------|----------|
| `CrisisLevel` (Green→Black) | Retain as fallback for legacy escalation; new logic prioritizes distress-type → persona blend |
| `crisis_thresholds.yaml` | Retain; extend later with `distress_inputs` if desired; primary persona mapping in `persona_weights.yaml` |
| `CrisisDetector`, `CrisisAssessor` imports | Remove; replaced by `CrisisDetectionEngine` (CDE) |
| `InterventionManager`, `DeEscalationEngine` | Stub or defer; RRT refactor focuses on TOI/Fusion/CDE first |
| `SupervisorInterface`, `PatternAnalyzer` | Stub for integration; full implementation in ecosystem phase |

---

## 4. Data Flow Summary

1. **User** → provides TOI config (optional) and engages with RRT.
2. **TOI Parser** → loads/parses TOI, produces `TOIConfig`.
3. **Stage 1** → `StageHandlers.handle_stage_1_consent_prompt()` requests consent.
4. **Stage 2** → User selects distress input (e.g., "Everything hurts / Meltdown").
5. **Fusion Engine** → `compute_blend(distress_input)` → `PersonaBlend`.
6. **OTOI Coordinator** → applies TOI overrides to blend.
7. **Tone Profile** → `ToneProfileLoader.get_instructions(toi.tone_profile)` for prompt.
8. **CDE** (optional/parallel) → 3-layer analysis on free text; can suggest `distress_key` for Fusion.

---

## 5. NLT Guardrails Reflected in Code

- **Local-First**: CDE processes only local; no cloud calls.
- **Anti-Gaslight**: `validate_for_response()`; naming avoids blame.
- **No Forced Productivity**: `no_forced_productivity` in TOI blocks task-push when burnout signaled.
- **Agency First**: Stage 1 consent prompt before full RRT activation.

---

## 6. Next Step: JSON Schemas / YAML for TOI-OTOI

Gemini offered: *"Would you like me to initiate the generation of specific JSON schemas or YAML configurations for the TOI/OTOI layer that Cursor can directly ingest?"*

**Response:** The following YAML configurations are in place and ingestible:

- `config/toi_schema.yaml` – TOI structure and defaults
- `config/persona_weights.yaml` – Stage 2 distress → persona weights
- `config/tone_profiles.yaml` – Tone profile instructions

A JSON Schema for TOI validation can be added in a follow-up if desired.
