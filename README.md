# RRT Advocate

**Rapid Response Team Advocate - Crisis Intervention & Immediate ADHD Support**

## Mission

The RRT (Rapid Response Team) Advocate is a specialized AI agent within the NeuroLift Technologies ecosystem, designed to provide immediate, crisis-level support for individuals experiencing acute ADHD-related challenges. This Advocate represents the fusion of Avatar and Aide intelligences specifically trained for rapid response scenarios.

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
├── rrt_advocate.py      # Main RRT Advocate (Solidarity Framework integrated)
├── governance/          # TOI-OTOI layer
├── persona/             # Persona Fusion Engine (5 OGs)
├── dialogue/            # Tiered Activation Dialogue Tree
├── prompts/             # Tone profiles for LLM prompts
├── crisis/              # Crisis Detection Engine (3-layer CDE)
├── response/            # Interventions, de-escalation
├── coordination/        # Supervisor interface
└── learning/            # Pattern analyzer

config/
├── crisis_thresholds.yaml   # Crisis detection parameters
├── toi_schema.yaml         # TOI configuration schema
├── persona_weights.yaml    # Distress input → persona weights
└── tone_profiles.yaml     # Tone profile instructions

docs/
├── crisis_protocols.md       # Crisis response documentation
├── integration_guide.md      # NeuroLift ecosystem integration
├── training_methodology.md   # Avatar-Aide fusion process
└── privacy_security.md       # Privacy and security specifications

tests/
├── crisis_simulation/        # Crisis scenario testing
├── response_validation/      # Response effectiveness testing
└── integration_tests/        # Ecosystem integration testing
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

**Current Phase**: Solidarity Framework Integration (Protective Layer)

The RRT Advocate has been upgraded as the **RRT AIdvocAIte** — the Protective Layer of the HAIEF Solidarity Framework. Key components:

- **TOI-OTOI Governance Wrapper**: User's Terms of Interaction as strict middleware
- **Persona Fusion Engine**: Dynamic blending of Ash, Sol, Echo, Kai, Myra (5 OGs)
- **Tiered Activation Dialogue Tree**: Stage 0–5 user-led journey with consent gate
- **Configurable Tone Profiles**: Supportive Default, Minimal, Directive, Therapeutic/Reflective
- **3-Layer Crisis Detection Engine (CDE)**: Local-first keyword/semantic, sentiment, behavioral analysis

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
```bash
# From project root
PYTHONPATH=src python3 run_rrt.py
```

```python
from rrt_advocate import RRTAdvocate, create_rrt_advocate

# Initialize RRT Advocate (Solidarity Framework integrated)
advocate = await create_rrt_advocate("user_001")

# Stage 1: Agency-first consent prompt
prompt = advocate.get_stage_1_consent_prompt()

# Stage 2: Process distress input → Persona blend
blend = advocate.process_stage_2_input("Everything hurts / Meltdown")

# 3-layer CDE: Local-first crisis detection from text
cde_result = advocate.detect_crisis_from_text("I can't do anything. Everything hurts.")

# Tone instructions for LLM prompt construction
tone = advocate.get_tone_instructions()
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
