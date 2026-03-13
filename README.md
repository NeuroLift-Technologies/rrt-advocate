# RRT Advocate

**Rapid Response Team Advocate - Protective Layer (RRT AIdvocAIte)**

## Mission

The RRT (Rapid Response Team) Advocate is the Protective Layer implementation of the HAIEF Solidarity Framework, designed for immediate support during neurodivergent distress while preserving user agency and privacy.

## Core Purpose

**"When ADHD overwhelms, RRT responds"**

The RRT Advocate serves as the first-line digital responder for:
- **Executive Function Crises**: Sudden inability to organize, prioritize, or initiate tasks
- **Emotional Dysregulation Events**: Intense overwhelm, rejection sensitivity, or emotional flooding
- **Attention Collapse**: Complete loss of focus or hyperfocus breaking unexpectedly
- **Time Blindness Emergencies**: Critical deadline awareness or time management failures
- **Decision Paralysis**: Inability to make choices leading to functional shutdown

## Architecture Overview

### AI-Fusion Framework Integration

The RRT Advocate follows the proprietary NeuroLift AI-fusion methodology:

```
Crisis Avatar + Emergency Aide → RRT Advocate
```

**Crisis Avatar Training Environment:**
- Simulated high-stress ADHD scenarios in virtual environments
- Rapid decision-making under pressure
- Pattern recognition for crisis indicators
- Self-advocacy and immediate coping strategies

**Emergency Aide Development:**
- Empathetic crisis response protocols
- De-escalation techniques for ADHD-specific triggers
- Resource mobilization and support coordination
- Real-time environmental adaptation

**Fused RRT Advocate Capabilities:**
- Immediate crisis assessment and triage
- Rapid deployment of coping strategies
- Escalation protocols for severe situations
- Integration with broader NeuroLift ecosystem

## Key Features

### 🚨 Crisis Detection & Response
- **Real-time Monitoring**: Continuous assessment of user stress indicators
- **Trigger Recognition**: Pattern matching for ADHD crisis precursors
- **Immediate Intervention**: Sub-second response time for critical situations
- **Escalation Protocols**: Seamless handoff to appropriate support systems

### 🧠 ADHD-Specific Crisis Management
- **Executive Function Rescue**: Emergency task breakdown and prioritization
- **Emotional Regulation Support**: Immediate grounding and regulation techniques
- **Attention Restoration**: Rapid focus recovery strategies
- **Time Crisis Management**: Emergency time awareness and deadline support

### 🔒 Privacy-First Crisis Support
- **Local Processing**: Crisis detection without data transmission
- **Encrypted Communications**: Secure crisis reporting and escalation
- **User Agency**: Complete control over crisis response preferences
- **Confidential Logging**: Private crisis pattern analysis for improvement

### 🤝 Ecosystem Integration
- **Supervisor AI Coordination**: Seamless integration with NeuroLift command structure
- **Multi-Advocate Collaboration**: Coordination with specialized Advocates
- **External Resource Access**: Connection to crisis hotlines and professional support
- **Family/Caregiver Alerts**: Configurable emergency contact protocols

## Repository Structure

```
src/
├── rrt_advocate.py            # Main TOI-governed orchestration entrypoint
├── toi_otoi.py                # TOI parser + OTOI persona coordination
├── persona_fusion.py          # Dynamic 5-persona weighting engine
├── tone_profiles.py           # Configurable tone profile prompt shaping
├── crisis_detection_engine.py # Local-first 3-layer CDE pipeline
└── dialogue_tree.py           # Tiered activation stages 0-5

config/
└── crisis_thresholds.yaml     # TOI defaults, stage mapping, CDE, tones

tests/
└── test_protective_layer.py   # Coverage for consent, mapping, tones, CDE
```

## Development Philosophy

### Crisis-First Design
Every component is designed with crisis response as the primary consideration:
- **Speed Over Perfection**: Rapid response prioritized over comprehensive analysis
- **Fail-Safe Defaults**: Conservative escalation when uncertain
- **User Safety Priority**: All decisions prioritize user wellbeing
- **Continuous Availability**: 24/7 crisis monitoring and response capability

### ADHD-Informed Crisis Understanding
The RRT Advocate is built with deep understanding of ADHD-specific crisis patterns:
- **Rejection Sensitive Dysphoria**: Specialized protocols for RSD episodes
- **Executive Function Collapse**: Targeted support for cognitive overwhelm
- **Hyperfocus Interruption**: Gentle transition strategies
- **Time Blindness Crises**: Emergency time awareness restoration

### Privacy-First Crisis Support
Crisis situations require maximum privacy protection:
- **Local Crisis Detection**: No external data transmission for assessment
- **Encrypted Crisis Logs**: Secure storage of crisis patterns
- **User-Controlled Escalation**: Complete control over external contact
- **Anonymous Crisis Reporting**: Optional anonymous data for system improvement

## Integration with NeuroLift Ecosystem

### Supervisor AI Coordination
```python
# Example integration with Supervisor AI
class RRTAdvocate:
    def report_crisis(self, crisis_assessment):
        """Report crisis to Supervisor AI for ecosystem coordination"""
        return self.supervisor.handle_crisis(
            advocate_id="rrt",
            crisis_level=crisis_assessment.severity,
            required_advocates=crisis_assessment.support_needed,
            user_preferences=self.user.crisis_preferences
        )
```

### Multi-Advocate Collaboration
The RRT Advocate coordinates with other specialized Advocates:
- **StayAlert Advocate**: For attention-related crises
- **ImpulseGuard Advocate**: For decision-making emergencies
- **FocusFlow Advocate**: For hyperfocus management crises
- **Timely Advocate**: For time blindness emergencies

## Development Status

**Current Phase**: Protective Layer Transformation (TOI/OTOI Compliant)

This repository now includes TOI-first consent gating, OTOI persona arbitration, dynamic persona fusion (Ash/Sol/Echo/Kai/Myra), configurable tone profiles, and a local-first three-layer Crisis Detection Engine.

## Getting Started

### Prerequisites
- Python 3.9+
- NeuroLift Supervisor AI (for ecosystem integration)
- Crisis response training data
- ADHD-specific crisis pattern datasets

### Installation
```bash
# Clone the repository
git clone https://github.com/JDUB1216/rrt-advocate.git
cd rrt-advocate

# Install dependencies
pip install -r requirements.txt

# Configure crisis detection parameters
cp config/crisis_thresholds.example.yaml config/crisis_thresholds.yaml
# Edit configuration files as needed

# Run initial setup
python setup.py install
```

### Quick Start
```python
from rrt_advocate import RRTAdvocate

rrt = RRTAdvocate(user_id="demo", config_path="config/crisis_thresholds.yaml")
rrt.ingest_toi({
    "tone_profile": "supportive_default",
    "pacing": "steady",
    "cognitive_scaffolding": "moderate",
    "safety_boundaries": ["No shaming language"],
})

# Stage 1: consent
rrt.handle_stage1_consent(True)

# Stage 2/3: distress routing + persona fusion + CDE analysis
response = rrt.handle_stage2_distress(
    distress_input="can't do basic tasks",
    user_message="I can't start anything",
)
print(response["message"])
```

## Contributing

The RRT Advocate is part of the proprietary NeuroLift Technologies AI-fusion framework. Development follows established protocols for specialized Advocate creation.

### Development Guidelines
1. **Crisis-First Thinking**: Every feature must consider crisis response impact
2. **ADHD-Informed Design**: All development informed by ADHD research and lived experience
3. **Privacy by Design**: Privacy considerations integrated from initial design
4. **Fail-Safe Implementation**: Conservative defaults that prioritize user safety

## Privacy & Security

The RRT Advocate handles sensitive crisis data and implements comprehensive privacy protections:
- **Local Processing**: Crisis detection and initial response processed locally
- **Encrypted Storage**: All crisis logs encrypted with user-controlled keys
- **Minimal Data Collection**: Only essential data collected for crisis response
- **User-Controlled Sharing**: Complete user control over crisis data sharing

## License

This repository contains proprietary NeuroLift Technologies intellectual property. The AI-fusion framework and specialized Advocate development methodology are protected under applicable intellectual property laws.

## Support & Crisis Resources

### Immediate Crisis Support
If you are experiencing a mental health crisis:
- **US**: National Suicide Prevention Lifeline: 988
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911

### ADHD-Specific Resources
- **CHADD**: Children and Adults with ADHD - chadd.org
- **ADDitude Magazine**: additudemag.com
- **ADHD Online Community**: reddit.com/r/ADHD

---

**NeuroLift Technologies**  
*Tech That Gets You • Nothing About Us Without Us • ElevAIte Your Mind*  
*Elevating Mind, Changing Lives*
