"""
GEMINI_TOPOGRAPHY.py
RRT AIdvocAIte — Protective Layer of the Solidarity Framework

Repository metadata and structural mapping for AI assistants.
Updated to reflect the TOI-compliant, multi-persona orchestration
architecture.
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


REPOSITORY_INFO = {
    "name": "rrt-advocate",
    "full_name": "RRT AIdvocAIte — Protective Layer of the Solidarity Framework",
    "description": (
        "TOI-compliant, dynamically weighted, multi-persona orchestration "
        "engine for neurodivergent crisis support within the NeuroLift "
        "Technologies Solidarity Framework."
    ),
    "github_url": "https://github.com/NeuroLift-Technologies/rrt-advocate",
    "created_date": "2025-09-26",
    "current_date": "2026-03-13",
    "visibility": "Private",
    "status": "Solidarity Framework Integration — Active Development",
    "purpose": "Protective Layer: crisis intervention via multi-persona fusion",
    "ecosystem_role": "RRT AIdvocAIte within the HAIEF Solidarity Framework",
    "framework_layer": "Protective Layer",
    "framework_components": [
        "TOI-OTOI Governance Wrapper",
        "Persona Fusion Engine (5 OG personas)",
        "Crisis Detection Engine (3-layer, local-first)",
        "Tiered Activation Dialogue Tree (Stages 0–5)",
        "Configurable Tone Profiles (4 modes)",
    ],
}


class PersonaType(Enum):
    ASH = "ash"
    SOL = "sol"
    ECHO = "echo"
    KAI = "kai"
    MYRA = "myra"


class CrisisLevel(Enum):
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


SOLIDARITY_FRAMEWORK = {
    "constitutional_layer": {
        "toi": "Terms of Interaction — user's explicit interaction contract",
        "otoi": "Orchestrated TOI — multi-persona coordination governance",
    },
    "protective_layer": {
        "rrt_aidvocaite": "This repository — crisis intervention engine",
        "sleepwalker_protocol": "Companion protocol (separate repo)",
    },
}


PERSONA_REGISTRY = {
    "ash": {
        "display_name": "Ash",
        "core_role": "Validates burnout, diffuses shame, prioritises being over doing",
        "activates_for": ["meltdown", "burnout", "shutdown"],
        "tone_affinity": ["supportive", "therapeutic"],
    },
    "sol": {
        "display_name": "Sol",
        "core_role": "Scaffolds executive function, breaks down tasks, manages attention fatigue",
        "activates_for": ["cant_do_tasks", "overwhelm"],
        "tone_affinity": ["directive", "minimal"],
    },
    "echo": {
        "display_name": "Echo",
        "core_role": "Mirrors internal monologue, reframes cognitive distortions",
        "activates_for": ["self_blame", "negative_self_talk"],
        "tone_affinity": ["therapeutic", "supportive"],
    },
    "kai": {
        "display_name": "Kai",
        "core_role": "Redirects hyperfocus and fixation into constructive pathways",
        "activates_for": ["hyperfocus_loop"],
        "tone_affinity": ["directive", "minimal"],
    },
    "myra": {
        "display_name": "Myra",
        "core_role": "Provides relational safety, co-regulation, anchors Silent Mode",
        "activates_for": ["shutdown", "relational_distress", "meltdown"],
        "tone_affinity": ["supportive", "therapeutic"],
    },
}


@dataclass
class DirectoryInfo:
    name: str
    purpose: str
    key_files: List[str]
    dependencies: List[str]
    integration_points: List[str]


REPOSITORY_STRUCTURE = {
    "src/": DirectoryInfo(
        name="Source Code Root",
        purpose="Core RRT AIdvocAIte implementation",
        key_files=["__init__.py", "rrt_advocate.py"],
        dependencies=["config/"],
        integration_points=["All sub-packages"],
    ),
    "src/toi/": DirectoryInfo(
        name="TOI-OTOI Governance Wrapper",
        purpose="Terms of Interaction middleware and OTOI coordination",
        key_files=["toi_config.py", "toi_parser.py", "otoi_coordinator.py"],
        dependencies=["config/toi_defaults.yaml"],
        integration_points=["Persona Fusion Engine", "Dialogue Tree"],
    ),
    "src/personas/": DirectoryInfo(
        name="Persona Fusion Engine",
        purpose="5 OG personas and dynamic weighting algorithm",
        key_files=[
            "persona_base.py", "ash.py", "sol.py", "echo.py",
            "kai.py", "myra.py", "fusion_engine.py",
        ],
        dependencies=["config/persona_weights.yaml"],
        integration_points=["OTOI Coordinator", "Dialogue Tree"],
    ),
    "src/dialogue/": DirectoryInfo(
        name="Tiered Activation Dialogue Tree",
        purpose="Agency-first staged interaction flow (Stages 0–5)",
        key_files=["dialogue_tree.py", "stage_handlers.py", "consent_manager.py"],
        dependencies=["src/personas/", "src/toi/"],
        integration_points=["RRT Advocate orchestrator"],
    ),
    "src/detection/": DirectoryInfo(
        name="Crisis Detection Engine (CDE)",
        purpose="3-layer, local-first crisis detection pipeline",
        key_files=[
            "cde_pipeline.py", "keyword_analyzer.py",
            "sentiment_analyzer.py", "behavioral_analyzer.py",
        ],
        dependencies=["config/crisis_thresholds.yaml"],
        integration_points=["RRT Advocate orchestrator"],
    ),
    "src/tones/": DirectoryInfo(
        name="Configurable Tone Profiles",
        purpose="4 communication style presets",
        key_files=["tone_profiles.py"],
        dependencies=["config/tone_profiles.yaml"],
        integration_points=["TOI Parser", "Persona Fusion Engine"],
    ),
    "config/": DirectoryInfo(
        name="Configuration",
        purpose="YAML configs for CDE, TOI, personas, and tones",
        key_files=[
            "crisis_thresholds.yaml", "toi_defaults.yaml",
            "persona_weights.yaml", "tone_profiles.yaml",
        ],
        dependencies=[],
        integration_points=["All source modules"],
    ),
    "tests/": DirectoryInfo(
        name="Test Suite",
        purpose="Comprehensive pytest suite for all components",
        key_files=[
            "test_toi.py", "test_fusion_engine.py", "test_cde.py",
            "test_dialogue_tree.py", "test_tone_profiles.py",
            "test_rrt_advocate.py",
        ],
        dependencies=["src/"],
        integration_points=["CI/CD pipeline"],
    ),
}


CDE_SPECIFICATION = {
    "layer_1_keyword_semantic": {
        "purpose": "Lexicon-based keyword matching against curated semantic fields",
        "fields": [
            "negative_self_talk", "task_avoidance", "overwhelm",
            "hyperfocus_loop", "relational_distress",
        ],
        "weight_in_aggregate": 0.40,
        "local_only": True,
    },
    "layer_2_sentiment_tone": {
        "purpose": "Polarity tracking, drop detection, emotional volatility",
        "metrics": ["polarity", "magnitude", "polarity_drop", "volatility", "trend"],
        "weight_in_aggregate": 0.30,
        "local_only": True,
    },
    "layer_3_behavioral_pattern": {
        "purpose": "Response latency, message complexity, conversational looping",
        "metrics": ["latency_score", "complexity_score", "looping_score"],
        "weight_in_aggregate": 0.30,
        "local_only": True,
    },
}


DEVELOPMENT_APPROACH = {
    "core_principles": [
        "Local-First & Privacy-Centric",
        "Agency First (consent before engagement)",
        "Anti-Gaslight / Shame-Resistant Design",
        "No Forced Productivity",
        "TOI-Compliant (every response filtered)",
    ],
    "testing_strategy": {
        "framework": "pytest",
        "test_count": "117+",
        "coverage_areas": [
            "TOI-OTOI Governance Wrapper",
            "Persona Fusion Engine (all 5 personas + blending)",
            "Crisis Detection Engine (all 3 layers + pipeline)",
            "Tiered Activation Dialogue Tree (all stages)",
            "Configurable Tone Profiles",
            "Full integration flow",
        ],
    },
}


def get_repository_overview() -> Dict[str, Any]:
    return {
        "metadata": REPOSITORY_INFO,
        "solidarity_framework": SOLIDARITY_FRAMEWORK,
        "persona_registry": PERSONA_REGISTRY,
        "structure": REPOSITORY_STRUCTURE,
        "cde_specification": CDE_SPECIFICATION,
        "development_approach": DEVELOPMENT_APPROACH,
    }


def validate_repository_structure() -> Dict[str, bool]:
    base_path = os.path.dirname(os.path.abspath(__file__))
    required_paths = [
        "src/",
        "src/toi/",
        "src/personas/",
        "src/dialogue/",
        "src/detection/",
        "src/tones/",
        "config/",
        "tests/",
    ]
    return {
        path: os.path.exists(os.path.join(base_path, path))
        for path in required_paths
    }


if __name__ == "__main__":
    print("RRT AIdvocAIte — Repository Topography")
    print("=" * 50)

    overview = get_repository_overview()
    print(f"Repository: {overview['metadata']['name']}")
    print(f"Purpose: {overview['metadata']['purpose']}")
    print(f"Status: {overview['metadata']['status']}")
    print(f"Framework Layer: {overview['metadata']['framework_layer']}")

    print("\nComponents:")
    for comp in overview["metadata"]["framework_components"]:
        print(f"  • {comp}")

    print("\nPersonas:")
    for pid, info in PERSONA_REGISTRY.items():
        print(f"  • {info['display_name']}: {info['core_role']}")

    print("\nStructure Validation:")
    for path, exists in validate_repository_structure().items():
        print(f"  {'✓' if exists else '✗'} {path}")
