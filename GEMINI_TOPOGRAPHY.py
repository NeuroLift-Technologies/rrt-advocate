"""
GEMINI_TOPOGRAPHY.py
RRT Advocate Repository - Topography and Data Mapping

This file provides comprehensive guidance for Gemini AI on the repository structure,
development context, and integration with the NeuroLift Technologies ecosystem.
The RRT (Rapid Response Team) Advocate is a specialized crisis intervention AI agent.

Repository: https://github.com/NeuroLift-Technologies/rrt-advocate

Source-of-truth note: use README.md and docs/integration_guide.md for the
current code-verified runtime interfaces. Planning dictionaries in this file are
context, not production deployment promises.
"""

import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# ============================================================================
# REPOSITORY METADATA
# ============================================================================

REPOSITORY_INFO = {
    "name": "rrt-advocate",
    "full_name": "Rapid Response Team Advocate",
    "description": "Specialized AI agent for crisis intervention and immediate ADHD support within the NeuroLift ecosystem",
    "github_url": "https://github.com/NeuroLift-Technologies/rrt-advocate",
    "notion_project": "https://www.notion.so/27a555e42dea8153b5eddae9b4c85ef3",  # To be created in Phase 4
    "created_date": "2025-09-26",
    "current_date": "2026-06-22",
    "visibility": "Private",
    "status": "Runtime/documentation alignment",
    "purpose": "Crisis intervention and immediate ADHD support",
    "ecosystem_role": "Protective Layer within the Solidarity Framework",
    "current_runtime_surfaces": [
        "Python protective layer in src/rrt_advocate.py and local src/* modules",
        "TypeScript CDE package in packages/rrt-advocate/",
        "Cloudflare Worker assistant in src/index.ts and public/"
    ]
}

# ============================================================================
# NEUROLIFT ECOSYSTEM CONTEXT
# ============================================================================

class AdvocateType(Enum):
    """Types of Advocates in the NeuroLift ecosystem"""
    CRISIS_RESPONSE = "rrt"
    ATTENTION_SUPPORT = "stayalert"
    IMPULSE_MANAGEMENT = "impulseguard"
    FOCUS_OPTIMIZATION = "focusflow"
    TIME_MANAGEMENT = "timely"
    DEVELOPER_SUPPORT = "developer"
    SUPERVISOR = "supervisor"

class CrisisLevel(Enum):
    """Crisis severity levels for RRT Advocate response"""
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"

NEUROLIFT_INTEGRATION = {
    "ecosystem_position": {
        "role": "Crisis Response Specialist",
        "priority": "Highest (Emergency Response)",
        "activation_trigger": "Crisis detection or manual emergency activation",
        "coordination_level": "System-wide (can activate any Advocate)"
    },
    "ai_fusion_framework": {
        "avatar_training": {
            "environment": "High-stress ADHD crisis simulations",
            "scenarios": [
                "Executive function collapse",
                "Emotional dysregulation events",
                "Attention system failures",
                "Time blindness emergencies",
                "Decision paralysis situations"
            ],
            "learning_objectives": [
                "Rapid crisis assessment",
                "Immediate coping strategy deployment",
                "Self-advocacy under pressure",
                "Pattern recognition for crisis indicators"
            ]
        },
        "aide_development": {
            "focus": "Emergency response and de-escalation",
            "capabilities": [
                "Empathetic crisis response",
                "De-escalation techniques",
                "Resource mobilization",
                "Environmental adaptation",
                "Support coordination"
            ],
            "training_data": [
                "ADHD crisis intervention protocols",
                "Mental health first aid procedures",
                "Neurodivergent-specific support strategies",
                "Emergency response best practices"
            ]
        },
        "fusion_result": {
            "name": "RRT Advocate",
            "specialization": "Crisis intervention and immediate ADHD support",
            "unique_capabilities": [
                "Sub-second crisis assessment",
                "ADHD-informed intervention strategies",
                "Multi-system coordination during crises",
                "Privacy-preserving emergency response"
            ]
        }
    },
    "related_repositories": {
        "neurolift-ai-fusion": {
            "relationship": "Parent ecosystem",
            "integration_points": [
                "Supervisor AI coordination",
                "Multi-Advocate collaboration protocols",
                "Shared user profile and preferences"
            ]
        },
        "nlt-otoi": {
            "relationship": "Foundational framework",
            "integration_status": "Testing phase (separate development structure)",
            "future_integration": "Full TOI-OTOI framework integration planned"
        },
        "personal-data-manager": {
            "relationship": "Data source",
            "integration_points": [
                "Crisis pattern analysis",
                "Historical response effectiveness",
                "User preference learning"
            ]
        }
    }
}

# ============================================================================
# REPOSITORY STRUCTURE DEFINITION
# ============================================================================

@dataclass
class DirectoryInfo:
    """Information about a directory in the repository"""
    name: str
    purpose: str
    key_files: List[str]
    dependencies: List[str]
    integration_points: List[str]

REPOSITORY_STRUCTURE = {
    "src/": DirectoryInfo(
        name="Source Code",
        purpose="Python protective layer plus root Cloudflare Worker entrypoint",
        key_files=["rrt_advocate.py", "index.ts", "types.ts"],
        dependencies=["config/", "public/", "docs/"],
        integration_points=["Host Python services", "Cloudflare Workers"]
    ),
    "src/crisis/": DirectoryInfo(
        name="Crisis Detection & Assessment",
        purpose="Python 3-layer crisis pattern recognition and severity assessment",
        key_files=[
            "detectors/keyword_layer.py",
            "detectors/sentiment_layer.py",
            "detectors/behavioral_layer.py",
            "detectors/crisis_detector.py",
            "assessors/crisis_assessor.py"
        ],
        dependencies=["config/crisis_thresholds.yaml"],
        integration_points=["RRTAdvocate.assess_current_state", "RRTAdvocate.process_message"]
    ),
    "src/dialogue/": DirectoryInfo(
        name="Tiered Dialogue Tree",
        purpose="Stage 0-5 activation journey and option selection",
        key_files=["stages.py", "dialogue_tree.py"],
        dependencies=["src/toi/", "src/personas/"],
        integration_points=["RRTAdvocate.process_message", "RRTAdvocate.select_stage_option"]
    ),
    "src/personas/": DirectoryInfo(
        name="Persona Fusion",
        purpose="Ash/Sol/Echo/Kai/Myra persona weighting and blended responses",
        key_files=["fusion_engine.py", "ash.py", "sol.py", "echo.py", "kai.py", "myra.py"],
        dependencies=["config/personas.yaml", "config/tone_profiles.yaml", "src/toi/"],
        integration_points=["DialogueTree", "InterventionManager", "DeEscalationEngine"]
    ),
    "src/toi/": DirectoryInfo(
        name="TOI/OTOI Governance",
        purpose="Terms of Interaction parsing, consent gate, and response filtering",
        key_files=["toi_models.py", "toi_parser.py", "otoi_middleware.py"],
        dependencies=["config/toi_defaults.yaml", "config/tone_profiles.yaml"],
        integration_points=["RRTAdvocate", "DialogueTree", "FusionEngine"]
    ),
    "src/response/": DirectoryInfo(
        name="Crisis Response Protocols",
        purpose="Intervention deployment and de-escalation orchestration",
        key_files=["interventions/intervention_manager.py", "de_escalation/de_escalation_engine.py"],
        dependencies=["src/personas/", "src/toi/"],
        integration_points=["RRTAdvocate.manual_intervention", "RRTAdvocate._handle_crisis"]
    ),
    "src/coordination/": DirectoryInfo(
        name="System Coordination",
        purpose="Supervisor callback contract and local supervisor implementation",
        key_files=["supervisor/supervisor_interface.py"],
        dependencies=["src/crisis/"],
        integration_points=["RRTAdvocate.start_monitoring", "RRTAdvocate._emergency_escalation"]
    ),
    "src/learning/": DirectoryInfo(
        name="Continuous Learning",
        purpose="Local session pattern analysis and persistence hooks",
        key_files=["patterns/pattern_analyzer.py"],
        dependencies=["RRTAdvocate user_id"],
        integration_points=["RRTAdvocate._monitoring_loop", "RRTAdvocate.shutdown"]
    ),
    "config/": DirectoryInfo(
        name="Configuration",
        purpose="Crisis thresholds, TOI defaults, persona definitions, and tone profiles",
        key_files=["crisis_thresholds.yaml", "toi_defaults.yaml", "personas.yaml", "tone_profiles.yaml"],
        dependencies=["Governance approval for safety-critical changes"],
        integration_points=["Python protective layer", "TypeScript CDE package threshold sync"]
    ),
    "packages/rrt-advocate/": DirectoryInfo(
        name="TypeScript CDE Package",
        purpose="@neurolift-technologies/rrt-advocate detection and assessment library",
        key_files=["package.json", "src/index.ts", "README.md", "KNOWN_LIMITATIONS.md"],
        dependencies=["Node >=20", "packages/rrt-advocate/config/crisis_thresholds.yaml"],
        integration_points=["npm consumers needing local detection/assessment only"]
    ),
    "public/": DirectoryInfo(
        name="Worker Browser UI",
        purpose="Static chat interface served by the Cloudflare Worker",
        key_files=["index.html", "chat.js"],
        dependencies=["src/index.ts", "wrangler.jsonc"],
        integration_points=["/api/chat", "/api/health"]
    ),
    "docs/": DirectoryInfo(
        name="Documentation",
        purpose="Crisis protocols, integration guides, and methodology documentation",
        key_files=["integration_guide.md", "rrt-aidvocaite-worker.md", "active-threads.md", "agent-log/README.md"],
        dependencies=["Source code", "OTOI governance"],
        integration_points=["Developer resources", "Training materials"]
    ),
    "tests/": DirectoryInfo(
        name="Testing Suite",
        purpose="Python unit/integration tests for CDE, TOI, dialogue, fusion, and RRT facade behavior",
        key_files=["test_cde.py", "test_toi.py", "test_dialogue_tree.py", "test_fusion_engine.py", "test_rrt_advocate.py"],
        dependencies=["pytest", "pytest-asyncio", "pyyaml"],
        integration_points=["CI/CD pipeline", "Quality assurance"]
    )
}

# ============================================================================
# CRISIS RESPONSE SPECIFICATIONS
# ============================================================================

CRISIS_RESPONSE_FRAMEWORK = {
    "detection_parameters": {
        "physiological_indicators": [
            "Heart rate variability",
            "Stress hormone levels",
            "Sleep pattern disruption",
            "Appetite changes"
        ],
        "behavioral_indicators": [
            "Task abandonment patterns",
            "Communication changes",
            "Social withdrawal",
            "Routine disruption"
        ],
        "cognitive_indicators": [
            "Decision-making delays",
            "Memory lapses",
            "Attention fragmentation",
            "Executive function failures"
        ],
        "emotional_indicators": [
            "Mood volatility",
            "Rejection sensitivity spikes",
            "Overwhelm expressions",
            "Emotional dysregulation"
        ]
    },
    "response_protocols": {
        "immediate_assessment": {
            "timeframe": "< 5 seconds",
            "actions": [
                "Crisis level determination",
                "Safety assessment",
                "Resource availability check",
                "User preference consultation"
            ]
        },
        "intervention_deployment": {
            "timeframe": "< 30 seconds",
            "strategies": [
                "Grounding techniques",
                "Breathing exercises",
                "Cognitive restructuring",
                "Environmental modifications"
            ]
        },
        "escalation_protocols": {
            "conditions": [
                "Crisis level RED or BLACK",
                "User request for external support",
                "Safety concerns identified",
                "Intervention ineffectiveness"
            ],
            "actions": [
                "Supervisor AI notification",
                "Additional Advocate activation",
                "External resource connection",
                "Emergency contact notification"
            ]
        }
    },
    "privacy_protections": {
        "data_handling": [
            "Local crisis detection processing",
            "Encrypted crisis log storage",
            "User-controlled data sharing",
            "Automatic data expiration"
        ],
        "communication_security": [
            "End-to-end encrypted messaging",
            "Secure crisis reporting",
            "Anonymous effectiveness tracking",
            "Privacy-preserving escalation"
        ]
    }
}

# ============================================================================
# DEVELOPMENT METHODOLOGY
# ============================================================================

DEVELOPMENT_APPROACH = {
    "framework_integration_strategy": {
        "current_phase": "Separate Development Structure",
        "rationale": "Testing TOI-OTOI framework integration methodology",
        "approach": [
            "Build initial RRT Advocate without full TOI-OTOI framework",
            "Document integration challenges and solutions",
            "Create comprehensive integration guidelines",
            "Develop reusable integration patterns"
        ],
        "future_integration": [
            "Full TOI-OTOI framework adoption",
            "Terms of Interaction customization",
            "Optimization Through Organized Intelligence implementation",
            "Seamless ecosystem integration"
        ]
    },
    "crisis_first_design": {
        "principles": [
            "Speed over perfection in crisis response",
            "Fail-safe defaults for uncertain situations",
            "User safety as highest priority",
            "24/7 availability and reliability"
        ],
        "implementation": [
            "Optimized crisis detection algorithms",
            "Pre-loaded intervention strategies",
            "Redundant escalation pathways",
            "Continuous system monitoring"
        ]
    },
    "adhd_informed_development": {
        "research_basis": [
            "Executive function research",
            "Emotional dysregulation studies",
            "ADHD crisis intervention best practices",
            "Neurodivergent user experience research"
        ],
        "lived_experience_integration": [
            "ADHD community feedback",
            "Crisis survivor input",
            "Caregiver perspective inclusion",
            "Professional clinician guidance"
        ]
    }
}

# ============================================================================
# INTEGRATION SPECIFICATIONS
# ============================================================================

INTEGRATION_REQUIREMENTS = {
    "supervisor_ai_interface": {
        "communication_protocol": "Real-time bidirectional messaging",
        "data_exchange": [
            "Crisis assessments",
            "Intervention outcomes",
            "Resource requests",
            "Escalation notifications"
        ],
        "coordination_functions": [
            "Multi-Advocate activation",
            "Resource allocation",
            "User preference enforcement",
            "System-wide crisis management"
        ]
    },
    "advocate_collaboration": {
        "coordination_scenarios": [
            "Multi-domain crisis (attention + time management)",
            "Escalated intervention requirements",
            "Specialized expertise needs",
            "Long-term crisis management"
        ],
        "communication_patterns": [
            "Crisis handoff protocols",
            "Collaborative intervention planning",
            "Shared user state management",
            "Coordinated response execution"
        ]
    },
    "external_integrations": {
        "crisis_resources": [
            "National Suicide Prevention Lifeline",
            "Crisis Text Line",
            "Local emergency services",
            "Mental health crisis centers"
        ],
        "professional_support": [
            "ADHD specialists",
            "Mental health professionals",
            "Crisis intervention teams",
            "Support group networks"
        ],
        "data_sources": [
            "Wearable device data",
            "Calendar and task systems",
            "Communication platforms",
            "Environmental sensors"
        ]
    }
}

# ============================================================================
# QUALITY ASSURANCE & TESTING
# ============================================================================

TESTING_FRAMEWORK = {
    "crisis_simulation": {
        "scenario_types": [
            "Executive function collapse",
            "Emotional dysregulation events",
            "Attention system failures",
            "Time blindness emergencies",
            "Decision paralysis situations"
        ],
        "testing_parameters": [
            "Response time measurement",
            "Intervention effectiveness",
            "Escalation accuracy",
            "User safety maintenance"
        ]
    },
    "integration_testing": {
        "ecosystem_components": [
            "Supervisor AI communication",
            "Multi-Advocate coordination",
            "External resource connection",
            "User interface integration"
        ],
        "validation_criteria": [
            "Seamless system integration",
            "Data consistency maintenance",
            "Privacy protection verification",
            "Performance requirement compliance"
        ]
    },
    "user_acceptance_testing": {
        "participant_groups": [
            "ADHD individuals with crisis experience",
            "Caregivers and family members",
            "Mental health professionals",
            "Crisis intervention specialists"
        ],
        "evaluation_metrics": [
            "Crisis response satisfaction",
            "Intervention effectiveness perception",
            "System trust and reliability",
            "Privacy and security confidence"
        ]
    }
}

# ============================================================================
# DEPLOYMENT & MONITORING
# ============================================================================

DEPLOYMENT_SPECIFICATIONS = {
    "availability_requirements": {
        "uptime_target": "99.99%",
        "response_time": "< 5 seconds for crisis assessment",
        "scalability": "Support for concurrent crisis situations",
        "redundancy": "Multi-region deployment with failover"
    },
    "monitoring_systems": {
        "performance_metrics": [
            "Crisis detection accuracy",
            "Response time measurements",
            "Intervention success rates",
            "System availability tracking"
        ],
        "safety_monitoring": [
            "False positive/negative rates",
            "Escalation appropriateness",
            "User safety incident tracking",
            "System failure impact assessment"
        ]
    },
    "continuous_improvement": {
        "data_collection": [
            "Crisis pattern analysis",
            "Response effectiveness tracking",
            "User feedback integration",
            "System performance optimization"
        ],
        "update_procedures": [
            "Crisis protocol refinement",
            "Intervention strategy enhancement",
            "Integration improvement",
            "Security update deployment"
        ]
    }
}

# ============================================================================
# NOTION INTEGRATION PREPARATION
# ============================================================================

NOTION_PROJECT_STRUCTURE = {
    "database_requirements": [
        "Crisis Response Log",
        "Intervention Effectiveness Tracking",
        "Development Milestone Tracking",
        "Integration Testing Results",
        "User Feedback Collection"
    ],
    "page_templates": [
        "Crisis Protocol Documentation",
        "Integration Guide Updates",
        "Testing Scenario Definitions",
        "Performance Monitoring Reports"
    ],
    "automation_workflows": [
        "GitHub change logging",
        "Crisis response reporting",
        "Performance metric tracking",
        "Development progress updates"
    ]
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_repository_overview() -> Dict[str, Any]:
    """Get comprehensive repository overview for AI understanding"""
    return {
        "metadata": REPOSITORY_INFO,
        "ecosystem_context": NEUROLIFT_INTEGRATION,
        "structure": REPOSITORY_STRUCTURE,
        "crisis_framework": CRISIS_RESPONSE_FRAMEWORK,
        "development_approach": DEVELOPMENT_APPROACH,
        "integration_requirements": INTEGRATION_REQUIREMENTS,
        "testing_framework": TESTING_FRAMEWORK,
        "deployment_specs": DEPLOYMENT_SPECIFICATIONS
    }

def get_crisis_response_capabilities() -> Dict[str, Any]:
    """Get detailed crisis response capabilities and protocols"""
    return CRISIS_RESPONSE_FRAMEWORK

def get_integration_requirements() -> Dict[str, Any]:
    """Get NeuroLift ecosystem integration requirements"""
    return INTEGRATION_REQUIREMENTS

def get_development_context() -> Dict[str, Any]:
    """Get development methodology and approach context"""
    return DEVELOPMENT_APPROACH

# ============================================================================
# REPOSITORY HEALTH CHECK
# ============================================================================

def validate_repository_structure() -> Dict[str, bool]:
    """Validate that required repository structure exists"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    required_paths = [
        "src/",
        "src/crisis/",
        "src/dialogue/",
        "src/personas/",
        "src/toi/",
        "src/response/",
        "src/coordination/",
        "src/learning/",
        "config/",
        "packages/rrt-advocate/",
        "public/",
        "docs/",
        "tests/"
    ]
    
    validation_results = {}
    for path in required_paths:
        full_path = os.path.join(base_path, path)
        validation_results[path] = os.path.exists(full_path)
    
    return validation_results

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("RRT Advocate Repository Topography")
    print("=" * 50)
    
    overview = get_repository_overview()
    print(f"Repository: {overview['metadata']['name']}")
    print(f"Purpose: {overview['metadata']['purpose']}")
    print(f"Status: {overview['metadata']['status']}")
    print(f"Ecosystem Role: {overview['metadata']['ecosystem_role']}")
    
    print("\nStructure Validation:")
    validation = validate_repository_structure()
    for path, exists in validation.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {path}")
    
    print(f"\nCrisis Response Capabilities: {len(CRISIS_RESPONSE_FRAMEWORK)} major components")
    print(f"Integration Points: {len(INTEGRATION_REQUIREMENTS)} integration categories")
    print(f"Testing Framework: {len(TESTING_FRAMEWORK)} testing categories")
