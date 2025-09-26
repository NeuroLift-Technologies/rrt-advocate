"""
RRT Advocate - Rapid Response Team Advocate
Main implementation for crisis intervention and immediate ADHD support

This module implements the core RRT Advocate functionality within the
NeuroLift Technologies AI-fusion framework.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json

# Crisis detection and response imports
from crisis.detectors.crisis_detector import CrisisDetector
from crisis.assessors.crisis_assessor import CrisisAssessor
from response.interventions.intervention_manager import InterventionManager
from response.de_escalation.de_escalation_engine import DeEscalationEngine
from coordination.supervisor.supervisor_interface import SupervisorInterface
from learning.patterns.pattern_analyzer import PatternAnalyzer

class CrisisLevel(Enum):
    """Crisis severity levels for response coordination"""
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"

class ResponseStatus(Enum):
    """Status of crisis response interventions"""
    PENDING = "pending"
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    ESCALATED = "escalated"
    FAILED = "failed"

@dataclass
class CrisisAssessment:
    """Comprehensive crisis assessment data structure"""
    timestamp: datetime
    crisis_level: CrisisLevel
    primary_indicators: List[str]
    secondary_indicators: List[str]
    confidence_score: float
    estimated_duration: Optional[timedelta]
    recommended_interventions: List[str]
    escalation_threshold: float
    user_safety_score: float
    context_factors: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InterventionResponse:
    """Response data from crisis intervention"""
    intervention_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: ResponseStatus
    effectiveness_score: Optional[float]
    user_feedback: Optional[str]
    side_effects: List[str] = field(default_factory=list)
    follow_up_required: bool = False

class RRTAdvocate:
    """
    Rapid Response Team Advocate - Crisis intervention specialist
    
    The RRT Advocate provides immediate crisis detection, assessment, and
    intervention for ADHD-related emergencies within the NeuroLift ecosystem.
    """
    
    def __init__(self, 
                 user_id: str,
                 config_path: str = "config/crisis_thresholds.yaml",
                 supervisor_interface: Optional[SupervisorInterface] = None):
        """
        Initialize RRT Advocate with user-specific configuration
        
        Args:
            user_id: Unique identifier for the user
            config_path: Path to crisis detection configuration
            supervisor_interface: Interface to NeuroLift Supervisor AI
        """
        self.user_id = user_id
        self.config_path = config_path
        self.supervisor = supervisor_interface
        
        # Initialize core components
        self.crisis_detector = CrisisDetector(config_path)
        self.crisis_assessor = CrisisAssessor(user_id)
        self.intervention_manager = InterventionManager(user_id)
        self.de_escalation_engine = DeEscalationEngine()
        self.pattern_analyzer = PatternAnalyzer(user_id)
        
        # State management
        self.is_monitoring = False
        self.current_crisis: Optional[CrisisAssessment] = None
        self.active_interventions: List[InterventionResponse] = []
        self.crisis_history: List[CrisisAssessment] = []
        
        # Performance tracking
        self.response_times: List[float] = []
        self.intervention_success_rate: float = 0.0
        self.last_assessment_time: Optional[datetime] = None
        
        # Setup logging
        self.logger = logging.getLogger(f"RRTAdvocate-{user_id}")
        self._setup_logging()
        
        self.logger.info(f"RRT Advocate initialized for user {user_id}")

    def _setup_logging(self):
        """Configure logging for crisis response tracking"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    async def start_monitoring(self) -> bool:
        """
        Start continuous crisis monitoring
        
        Returns:
            bool: True if monitoring started successfully
        """
        if self.is_monitoring:
            self.logger.warning("Crisis monitoring already active")
            return True
            
        try:
            self.is_monitoring = True
            self.logger.info("Starting crisis monitoring")
            
            # Start monitoring loop
            asyncio.create_task(self._monitoring_loop())
            
            # Notify supervisor of monitoring start
            if self.supervisor:
                await self.supervisor.notify_advocate_status(
                    advocate_id="rrt",
                    status="monitoring_active",
                    user_id=self.user_id
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            self.is_monitoring = False
            return False

    async def stop_monitoring(self) -> bool:
        """
        Stop crisis monitoring
        
        Returns:
            bool: True if monitoring stopped successfully
        """
        if not self.is_monitoring:
            return True
            
        try:
            self.is_monitoring = False
            self.logger.info("Stopping crisis monitoring")
            
            # Complete any active interventions
            for intervention in self.active_interventions:
                if intervention.status == ResponseStatus.ACTIVE:
                    await self._complete_intervention(intervention)
            
            # Notify supervisor
            if self.supervisor:
                await self.supervisor.notify_advocate_status(
                    advocate_id="rrt",
                    status="monitoring_stopped",
                    user_id=self.user_id
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")
            return False

    async def _monitoring_loop(self):
        """Main monitoring loop for continuous crisis detection"""
        while self.is_monitoring:
            try:
                # Perform crisis assessment
                assessment = await self.assess_current_state()
                
                # Handle crisis if detected
                if assessment.crisis_level != CrisisLevel.GREEN:
                    await self._handle_crisis(assessment)
                
                # Update pattern analysis
                await self.pattern_analyzer.update_patterns(assessment)
                
                # Brief pause before next assessment
                await asyncio.sleep(1)  # 1-second monitoring interval
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Longer pause on error

    async def assess_current_state(self) -> CrisisAssessment:
        """
        Perform comprehensive crisis assessment
        
        Returns:
            CrisisAssessment: Current crisis assessment
        """
        start_time = datetime.now()
        
        try:
            # Detect crisis indicators
            indicators = await self.crisis_detector.detect_crisis_indicators()
            
            # Assess crisis level and context
            assessment = await self.crisis_assessor.assess_crisis(indicators)
            
            # Record response time
            response_time = (datetime.now() - start_time).total_seconds()
            self.response_times.append(response_time)
            self.last_assessment_time = datetime.now()
            
            # Log assessment
            self.logger.info(
                f"Crisis assessment completed: {assessment.crisis_level.value} "
                f"(confidence: {assessment.confidence_score:.2f}, "
                f"response_time: {response_time:.3f}s)"
            )
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Crisis assessment failed: {e}")
            # Return safe default assessment
            return CrisisAssessment(
                timestamp=datetime.now(),
                crisis_level=CrisisLevel.GREEN,
                primary_indicators=[],
                secondary_indicators=[],
                confidence_score=0.0,
                estimated_duration=None,
                recommended_interventions=[],
                escalation_threshold=0.8,
                user_safety_score=1.0
            )

    async def _handle_crisis(self, assessment: CrisisAssessment):
        """
        Handle detected crisis with appropriate interventions
        
        Args:
            assessment: Crisis assessment data
        """
        self.current_crisis = assessment
        self.crisis_history.append(assessment)
        
        self.logger.warning(
            f"Crisis detected: {assessment.crisis_level.value} "
            f"(confidence: {assessment.confidence_score:.2f})"
        )
        
        try:
            # Immediate safety check
            if assessment.user_safety_score < 0.3:
                await self._emergency_escalation(assessment)
                return
            
            # Deploy appropriate interventions
            if assessment.crisis_level in [CrisisLevel.YELLOW, CrisisLevel.ORANGE]:
                await self._deploy_standard_interventions(assessment)
            elif assessment.crisis_level == CrisisLevel.RED:
                await self._deploy_intensive_interventions(assessment)
            elif assessment.crisis_level == CrisisLevel.BLACK:
                await self._emergency_escalation(assessment)
            
            # Notify supervisor of crisis
            if self.supervisor:
                await self.supervisor.handle_crisis(
                    advocate_id="rrt",
                    crisis_assessment=assessment,
                    user_id=self.user_id
                )
                
        except Exception as e:
            self.logger.error(f"Crisis handling failed: {e}")
            # Escalate on handling failure
            await self._emergency_escalation(assessment)

    async def _deploy_standard_interventions(self, assessment: CrisisAssessment):
        """Deploy standard crisis interventions"""
        for intervention_type in assessment.recommended_interventions:
            try:
                intervention = await self.intervention_manager.deploy_intervention(
                    intervention_type=intervention_type,
                    crisis_context=assessment.context_factors,
                    urgency_level="standard"
                )
                
                if intervention:
                    self.active_interventions.append(intervention)
                    self.logger.info(f"Deployed intervention: {intervention_type}")
                    
            except Exception as e:
                self.logger.error(f"Failed to deploy {intervention_type}: {e}")

    async def _deploy_intensive_interventions(self, assessment: CrisisAssessment):
        """Deploy intensive crisis interventions for high-severity situations"""
        # Start de-escalation process
        de_escalation_task = asyncio.create_task(
            self.de_escalation_engine.start_de_escalation(assessment)
        )
        
        # Deploy multiple interventions simultaneously
        intervention_tasks = []
        for intervention_type in assessment.recommended_interventions:
            task = asyncio.create_task(
                self.intervention_manager.deploy_intervention(
                    intervention_type=intervention_type,
                    crisis_context=assessment.context_factors,
                    urgency_level="intensive"
                )
            )
            intervention_tasks.append(task)
        
        # Wait for interventions to complete
        results = await asyncio.gather(*intervention_tasks, return_exceptions=True)
        
        # Process intervention results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Intervention {i} failed: {result}")
            elif result:
                self.active_interventions.append(result)
        
        # Wait for de-escalation
        await de_escalation_task

    async def _emergency_escalation(self, assessment: CrisisAssessment):
        """Handle emergency-level crisis escalation"""
        self.logger.critical(f"EMERGENCY ESCALATION: {assessment.crisis_level.value}")
        
        try:
            # Immediate supervisor notification
            if self.supervisor:
                await self.supervisor.emergency_escalation(
                    advocate_id="rrt",
                    crisis_assessment=assessment,
                    user_id=self.user_id
                )
            
            # Activate all available crisis resources
            await self.intervention_manager.activate_emergency_protocols(assessment)
            
            # Log emergency escalation
            self.logger.critical(
                f"Emergency protocols activated for user {self.user_id} "
                f"at {assessment.timestamp}"
            )
            
        except Exception as e:
            self.logger.critical(f"Emergency escalation failed: {e}")

    async def _complete_intervention(self, intervention: InterventionResponse):
        """Complete and evaluate an active intervention"""
        try:
            intervention.end_time = datetime.now()
            
            # Evaluate intervention effectiveness
            effectiveness = await self.intervention_manager.evaluate_intervention(
                intervention.intervention_id
            )
            
            intervention.effectiveness_score = effectiveness
            
            # Update success rate
            self._update_success_rate()
            
            # Remove from active interventions
            if intervention in self.active_interventions:
                self.active_interventions.remove(intervention)
            
            self.logger.info(
                f"Intervention {intervention.intervention_id} completed "
                f"(effectiveness: {effectiveness:.2f})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to complete intervention: {e}")

    def _update_success_rate(self):
        """Update intervention success rate based on recent performance"""
        if not self.crisis_history:
            return
        
        # Calculate success rate from recent interventions
        recent_interventions = [
            i for i in self.active_interventions 
            if i.end_time and i.effectiveness_score is not None
        ]
        
        if recent_interventions:
            success_count = sum(
                1 for i in recent_interventions 
                if i.effectiveness_score >= 0.7
            )
            self.intervention_success_rate = success_count / len(recent_interventions)

    async def get_status_report(self) -> Dict[str, Any]:
        """
        Get comprehensive status report for monitoring and debugging
        
        Returns:
            Dict containing current status and performance metrics
        """
        return {
            "user_id": self.user_id,
            "monitoring_active": self.is_monitoring,
            "current_crisis": {
                "level": self.current_crisis.crisis_level.value if self.current_crisis else "none",
                "confidence": self.current_crisis.confidence_score if self.current_crisis else 0.0
            },
            "active_interventions": len(self.active_interventions),
            "crisis_history_count": len(self.crisis_history),
            "performance": {
                "avg_response_time": sum(self.response_times[-100:]) / len(self.response_times[-100:]) if self.response_times else 0.0,
                "success_rate": self.intervention_success_rate,
                "last_assessment": self.last_assessment_time.isoformat() if self.last_assessment_time else None
            }
        }

    async def manual_intervention(self, intervention_type: str, context: Dict[str, Any] = None) -> bool:
        """
        Manually trigger a specific intervention
        
        Args:
            intervention_type: Type of intervention to deploy
            context: Additional context for the intervention
            
        Returns:
            bool: True if intervention was successfully deployed
        """
        try:
            self.logger.info(f"Manual intervention requested: {intervention_type}")
            
            intervention = await self.intervention_manager.deploy_intervention(
                intervention_type=intervention_type,
                crisis_context=context or {},
                urgency_level="manual"
            )
            
            if intervention:
                self.active_interventions.append(intervention)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Manual intervention failed: {e}")
            return False

    async def shutdown(self):
        """Gracefully shutdown the RRT Advocate"""
        self.logger.info("Shutting down RRT Advocate")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Save crisis history and patterns
        await self.pattern_analyzer.save_patterns()
        
        # Final status report
        status = await self.get_status_report()
        self.logger.info(f"Final status: {json.dumps(status, indent=2)}")
        
        self.logger.info("RRT Advocate shutdown complete")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def create_rrt_advocate(user_id: str, 
                            config_path: str = "config/crisis_thresholds.yaml",
                            supervisor_interface: Optional[SupervisorInterface] = None) -> RRTAdvocate:
    """
    Factory function to create and initialize RRT Advocate
    
    Args:
        user_id: Unique identifier for the user
        config_path: Path to crisis detection configuration
        supervisor_interface: Interface to NeuroLift Supervisor AI
        
    Returns:
        Initialized RRT Advocate instance
    """
    advocate = RRTAdvocate(user_id, config_path, supervisor_interface)
    
    # Perform initial system checks
    await advocate.assess_current_state()
    
    return advocate


# ============================================================================
# MAIN EXECUTION (for testing)
# ============================================================================

async def main():
    """Main function for testing RRT Advocate functionality"""
    print("RRT Advocate - Crisis Intervention System")
    print("=" * 50)
    
    # Create test advocate
    advocate = await create_rrt_advocate("test_user_001")
    
    try:
        # Start monitoring
        await advocate.start_monitoring()
        
        # Run for a short test period
        await asyncio.sleep(10)
        
        # Get status report
        status = await advocate.get_status_report()
        print(f"Status Report: {json.dumps(status, indent=2)}")
        
    finally:
        # Shutdown
        await advocate.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
