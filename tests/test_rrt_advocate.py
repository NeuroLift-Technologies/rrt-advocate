import asyncio
import importlib
import sys
import types
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


def _install_stub_modules():
    """Provide local stand-ins for external NeuroLift modules used by rrt_advocate."""

    class CrisisLevel(Enum):
        """Stand-in for crisis.assessors.crisis_assessor.CrisisLevel.

        rrt_advocate re-exports this enum, and the orchestrator branches on its
        members, so the stub must mirror the real five-level scale exactly.
        """

        GREEN = "stable"
        YELLOW = "elevated"
        ORANGE = "high"
        RED = "critical"
        BLACK = "emergency"

    @dataclass
    class CrisisIndicators:
        """Minimal stand-in for crisis.detectors.crisis_detector.CrisisIndicators.

        Mirrors the real dataclass's public, orchestrator-facing fields closely
        enough that src.rrt_advocate can import it and exercise the
        CDE -> TOI -> dialogue -> fusion -> OTOI path. Only the attributes the
        orchestrator actually reads (notably ``self_harm_risk``) need to behave
        like the production type; the rest carry the real defaults for fidelity.
        """

        timestamp: datetime = None
        raw_text: str = ""
        self_harm_risk: bool = False
        detected_semantic_fields: List[str] = field(default_factory=list)
        sentiment_trend: str = "stable"
        looping_detected: bool = False
        behavioral_complexity: float = 1.0
        aggregate_confidence: float = 0.0

    class CrisisDetector:
        def __init__(self, config_path):
            self.config_path = config_path

        async def detect_crisis_indicators(self, message=""):
            return CrisisIndicators(
                timestamp=datetime.now(),
                raw_text=message,
                self_harm_risk=False,
            )

    class CrisisAssessor:
        # Orchestrator constructs this as CrisisAssessor(user_id, config_path).
        def __init__(self, user_id, *_args, **_kwargs):
            self.user_id = user_id

        async def assess_crisis(self, _indicators):
            from src.rrt_advocate import CrisisAssessment, CrisisLevel

            return CrisisAssessment(
                timestamp=datetime.now(),
                crisis_level=CrisisLevel.GREEN,
                primary_indicators=[],
                secondary_indicators=[],
                confidence_score=0.2,
                estimated_duration=None,
                recommended_interventions=[],
                escalation_threshold=0.8,
                user_safety_score=1.0,
            )

    class ResponseStatus(Enum):
        """Stand-in for response.interventions.intervention_manager.ResponseStatus.

        rrt_advocate re-exports this enum (on InterventionResponse.status) and
        compares against ResponseStatus.ACTIVE, so the members must match.
        """

        PENDING = "pending"
        ACTIVE = "active"
        SUCCESSFUL = "successful"
        ESCALATED = "escalated"
        FAILED = "failed"

    class InterventionManager:
        # Orchestrator constructs this as
        # InterventionManager(user_id, toi_config, fusion_engine); accept extras.
        def __init__(self, user_id, *_args, **_kwargs):
            self.user_id = user_id

        async def deploy_intervention(self, **_kwargs):
            return None

        async def evaluate_intervention(self, _intervention_id):
            return 0.8

        async def activate_emergency_protocols(self, _assessment):
            return None

    class DeEscalationEngine:
        # Orchestrator constructs this as
        # DeEscalationEngine(toi_config, fusion_engine); accept extras.
        def __init__(self, *_args, **_kwargs):
            pass

        async def start_de_escalation(self, _assessment):
            return None

    class SupervisorInterface:
        async def notify_advocate_status(self, *_args, **_kwargs):
            return None

        async def handle_crisis(self, *_args, **_kwargs):
            return None

        async def emergency_escalation(self, *_args, **_kwargs):
            return None

    class LocalSupervisor(SupervisorInterface):
        """Default supervisor the orchestrator instantiates with LocalSupervisor()."""

        def __init__(self, *_args, **_kwargs):
            pass

    class PatternAnalyzer:
        def __init__(self, user_id):
            self.user_id = user_id

        async def update_patterns(self, _assessment):
            return None

        async def save_patterns(self):
            return None

        def get_summary(self):
            # Mirror the real PatternAnalyzer.get_summary() shape so
            # get_status_report() can serialize a pattern_summary block.
            return {
                "session_count": 0,
                "total_crisis_events": 0,
                "crisis_level_distribution": {},
            }

    module_defs = {
        "crisis": types.ModuleType("crisis"),
        "crisis.detectors": types.ModuleType("crisis.detectors"),
        "crisis.detectors.crisis_detector": types.ModuleType("crisis.detectors.crisis_detector"),
        "crisis.assessors": types.ModuleType("crisis.assessors"),
        "crisis.assessors.crisis_assessor": types.ModuleType("crisis.assessors.crisis_assessor"),
        "response": types.ModuleType("response"),
        "response.interventions": types.ModuleType("response.interventions"),
        "response.interventions.intervention_manager": types.ModuleType(
            "response.interventions.intervention_manager"
        ),
        "response.de_escalation": types.ModuleType("response.de_escalation"),
        "response.de_escalation.de_escalation_engine": types.ModuleType(
            "response.de_escalation.de_escalation_engine"
        ),
        "coordination": types.ModuleType("coordination"),
        "coordination.supervisor": types.ModuleType("coordination.supervisor"),
        "coordination.supervisor.supervisor_interface": types.ModuleType(
            "coordination.supervisor.supervisor_interface"
        ),
        "learning": types.ModuleType("learning"),
        "learning.patterns": types.ModuleType("learning.patterns"),
        "learning.patterns.pattern_analyzer": types.ModuleType("learning.patterns.pattern_analyzer"),
    }

    module_defs["crisis.detectors.crisis_detector"].CrisisDetector = CrisisDetector
    module_defs["crisis.detectors.crisis_detector"].CrisisIndicators = CrisisIndicators
    module_defs["crisis.assessors.crisis_assessor"].CrisisAssessor = CrisisAssessor
    module_defs["crisis.assessors.crisis_assessor"].CrisisLevel = CrisisLevel
    module_defs["response.interventions.intervention_manager"].InterventionManager = InterventionManager
    module_defs["response.interventions.intervention_manager"].ResponseStatus = ResponseStatus
    module_defs["response.de_escalation.de_escalation_engine"].DeEscalationEngine = DeEscalationEngine
    module_defs["coordination.supervisor.supervisor_interface"].SupervisorInterface = SupervisorInterface
    module_defs["coordination.supervisor.supervisor_interface"].LocalSupervisor = LocalSupervisor
    module_defs["learning.patterns.pattern_analyzer"].PatternAnalyzer = PatternAnalyzer

    sys.modules.update(module_defs)


def _load_module():
    _install_stub_modules()
    return importlib.import_module("src.rrt_advocate")


def test_get_status_report_has_expected_shape():
    module = _load_module()
    advocate = module.RRTAdvocate(user_id="user-1")

    status = asyncio.run(advocate.get_status_report())

    assert status["user_id"] == "user-1"
    assert status["monitoring_active"] is False
    assert status["current_crisis"]["level"] == "none"
    assert status["performance"]["avg_response_time"] == 0.0


def test_assess_current_state_returns_safe_default_on_detector_failure():
    module = _load_module()
    advocate = module.RRTAdvocate(user_id="user-2")

    async def broken_detector():
        raise RuntimeError("detector unavailable")

    advocate.crisis_detector.detect_crisis_indicators = broken_detector

    assessment = asyncio.run(advocate.assess_current_state())

    assert assessment.crisis_level == module.CrisisLevel.GREEN
    assert assessment.user_safety_score == 1.0
    assert assessment.confidence_score == 0.0


def test_manual_intervention_false_when_manager_returns_none():
    module = _load_module()
    advocate = module.RRTAdvocate(user_id="user-3")

    ok = asyncio.run(advocate.manual_intervention("grounding"))

    assert ok is False
    assert advocate.active_interventions == []
