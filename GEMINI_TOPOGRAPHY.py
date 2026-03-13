"""
GEMINI_TOPOGRAPHY.py
RRT AIdvocAIte — Protective Layer of the Solidarity Framework
Repository Topography and Data Mapping

This file provides comprehensive guidance for Gemini AI on the repository
structure, development context, and integration with the NeuroLift
Technologies ecosystem.

Repository: https://github.com/JDUB1216/rrt-advocate
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# REPOSITORY METADATA
# ============================================================================

REPOSITORY_INFO = {
    "name": "rrt-advocate",
    "full_name": "RRT AIdvocAIte — Protective Layer (Solidarity Framework)",
    "description": (
        "TOI-compliant, multi-persona crisis orchestration engine within the "
        "HAIEF Solidarity Framework.  Local-first, consent-first, agency-first."
    ),
    "github_url": "https://github.com/JDUB1216/rrt-advocate",
    "visibility": "Private",
    "status": "Active Development — Solidarity Framework Integration",
    "framework_role": "Protective Layer of the Solidarity Framework",
}

# ============================================================================
# SOLIDARITY FRAMEWORK CONTEXT
# ============================================================================

SOLIDARITY_FRAMEWORK = {
    "constitutional_layer": {
        "toi": "Terms of Interaction — user-defined interaction contract",
        "otoi": "Orchestrated TOI — multi-persona coordination under TOI",
    },
    "protective_layer": {
        "rrt_aidvocaite": "This repository — crisis intervention engine",
        "sleepwalker_protocol": "Companion safety net (separate repo)",
    },
}

# ============================================================================
# ARCHITECTURE COMPONENTS
# ============================================================================

COMPONENTS = {
    "toi_otoi_governance": {
        "path": "src/toi/",
        "files": ["toi_parser.py", "otoi_coordinator.py", "governance.py"],
        "purpose": "Middleware that enforces user's Terms of Interaction on all output",
    },
    "persona_fusion_engine": {
        "path": "src/personas/",
        "files": [
            "base.py", "ash.py", "sol.py", "echo.py",
            "kai.py", "myra.py", "fusion_engine.py",
        ],
        "purpose": "Dynamic weighting of the 5 Original Guides (0.0–1.0)",
        "personas": {
            "ASH": "Burnout validation, shame diffusion",
            "SOL": "Executive function scaffolding, task breakdown",
            "ECHO": "Cognitive reframing, negative self-talk mirrors",
            "KAI": "Hyperfocus/fixation redirection",
            "MYRA": "Relational safety, co-regulation, Silent Mode",
        },
    },
    "dialogue_tree": {
        "path": "src/dialogue/",
        "files": ["stages.py", "dialogue_tree.py"],
        "purpose": "Tiered Activation Dialogue (Stages 0-5), consent-first journey",
        "stages": [
            "Stage 0 — Detection (passive CDE monitoring)",
            "Stage 1 — Consent (entry prompt, user opt-in)",
            "Stage 2 — Assessment (5 low-demand distress options)",
            "Stage 3 — Support (persona-blended response)",
            "Stage 4 — Grounding (de-escalation exercises)",
            "Stage 5 — Transition (exit, follow-up, resources)",
        ],
    },
    "tone_profiles": {
        "path": "src/tone/",
        "files": ["profiles.py"],
        "purpose": "4 configurable tone profiles for LLM prompt engineering",
        "profiles": ["Supportive", "Minimal", "Directive", "Therapeutic"],
    },
    "crisis_detection_engine": {
        "path": "src/crisis/",
        "files": [
            "engine.py", "keyword_layer.py",
            "sentiment_layer.py", "behavioral_layer.py",
        ],
        "purpose": "3-layer local-first pipeline",
        "layers": [
            "Layer 1 — Keyword / Semantic Field Analysis",
            "Layer 2 — Sentiment & Emotional Tone (polarity drops)",
            "Layer 3 — Behavioural Pattern (latency, complexity, looping)",
        ],
    },
    "orchestrator": {
        "path": "src/rrt_advocate.py",
        "purpose": "Top-level wiring of all subsystems",
    },
    "shared_models": {
        "path": "src/models.py",
        "purpose": "Enums, dataclasses, type aliases used across all packages",
    },
}

# ============================================================================
# REPOSITORY STRUCTURE
# ============================================================================

REPOSITORY_STRUCTURE = """
src/
├── __init__.py
├── models.py                     # Shared data models
├── rrt_advocate.py               # Top-level orchestrator
├── toi/                          # TOI-OTOI Governance Wrapper
│   ├── toi_parser.py
│   ├── otoi_coordinator.py
│   └── governance.py
├── personas/                     # Persona Fusion Engine
│   ├── base.py
│   ├── ash.py  sol.py  echo.py  kai.py  myra.py
│   └── fusion_engine.py
├── dialogue/                     # Tiered Activation Dialogue Tree
│   ├── stages.py
│   └── dialogue_tree.py
├── tone/                         # Configurable Tone Profiles
│   └── profiles.py
└── crisis/                       # Crisis Detection Engine (CDE)
    ├── engine.py
    ├── keyword_layer.py
    ├── sentiment_layer.py
    └── behavioral_layer.py

config/
├── crisis_thresholds.yaml
├── toi_defaults.yaml
├── persona_weights.yaml
└── tone_profiles.yaml

tests/
├── test_toi_governance.py
├── test_fusion_engine.py
├── test_dialogue_tree.py
├── test_tone_profiles.py
├── test_crisis_engine.py
└── test_rrt_advocate.py

docs/
└── integration_guide.md
"""

# ============================================================================
# DESIGN PHILOSOPHY
# ============================================================================

DESIGN_PHILOSOPHY = {
    "local_first": "CDE processes everything on-device; no cloud by default",
    "anti_gaslight": "Non-judgmental naming, shame-resistant error handling",
    "no_forced_productivity": "Burnout = rest; never force task loops",
    "agency_first": "Stage 1 consent required before any intervention",
    "toi_compliance": "Every response passes through GOV middleware",
}

# ============================================================================
# HELPERS
# ============================================================================

def get_repository_overview() -> Dict[str, Any]:
    return {
        "metadata": REPOSITORY_INFO,
        "framework": SOLIDARITY_FRAMEWORK,
        "components": COMPONENTS,
        "design": DESIGN_PHILOSOPHY,
    }


def validate_repository_structure() -> Dict[str, bool]:
    base = os.path.dirname(os.path.abspath(__file__))
    paths = [
        "src/", "src/toi/", "src/personas/", "src/dialogue/",
        "src/tone/", "src/crisis/", "config/", "tests/", "docs/",
    ]
    return {p: os.path.exists(os.path.join(base, p)) for p in paths}


if __name__ == "__main__":
    print("RRT AIdvocAIte — Protective Layer Topography")
    print("=" * 55)
    ov = get_repository_overview()
    print(f"Repository : {ov['metadata']['name']}")
    print(f"Role       : {ov['metadata']['framework_role']}")
    print(f"Status     : {ov['metadata']['status']}")
    print()
    print("Structure Validation:")
    for path, ok in validate_repository_structure().items():
        print(f"  {'✓' if ok else '✗'} {path}")
