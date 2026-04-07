import asyncio
import importlib
import sys
import types
from datetime import datetime


def _install_stub_modules():
    """Provide local stand-ins for external NeuroLift modules used by rrt_advocate."""

    class CrisisDetector:
        def __init__(self, config_path):
            self.config_path = config_path

        async def detect_crisis_indicators(self):
            return {"signal": "ok"}

    class CrisisAssessor:
        def __init__(self, user_id):
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

    class InterventionManager:
        def __init__(self, user_id):
            self.user_id = user_id

        async def deploy_intervention(self, **_kwargs):
            return None

        async def evaluate_intervention(self, _intervention_id):
            return 0.8

        async def activate_emergency_protocols(self, _assessment):
            return None

    class DeEscalationEngine:
        async def start_de_escalation(self, _assessment):
            return None

    class SupervisorInterface:
        async def notify_advocate_status(self, **_kwargs):
            return None

        async def handle_crisis(self, **_kwargs):
            return None

        async def emergency_escalation(self, **_kwargs):
            return None

    class PatternAnalyzer:
        def __init__(self, user_id):
            self.user_id = user_id

        async def update_patterns(self, _assessment):
            return None

        async def save_patterns(self):
            return None

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
    module_defs["crisis.assessors.crisis_assessor"].CrisisAssessor = CrisisAssessor
    module_defs["response.interventions.intervention_manager"].InterventionManager = InterventionManager
    module_defs["response.de_escalation.de_escalation_engine"].DeEscalationEngine = DeEscalationEngine
    module_defs["coordination.supervisor.supervisor_interface"].SupervisorInterface = SupervisorInterface
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
