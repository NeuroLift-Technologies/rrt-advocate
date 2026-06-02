# RRT AIdvocAIte

**Real-Time Crisis Intervention & Protective Layer — Solidarity Framework**

> *"When burnout hits, the cavalry arrives."*

---


## Local Development (Repository Snapshot)

Because this repository references external NeuroLift modules that are not vendored here, runtime execution requires the broader ecosystem on `PYTHONPATH`. For this standalone snapshot, the fastest way to validate behavior is via the unit tests that use local stubs.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip pytest pytest-asyncio
pytest
```

Project tooling defaults are defined in `pyproject.toml`.

---

## What This Is

The RRT (Rapid Response Team) AIdvocAIte is the **Protective Layer** of the [Solidarity Framework](https://github.com/NeuroLift-Technologies) — a real-time crisis intervention system that detects when a user enters a state of burnout, distress, or emotional collapse and **actively intervenes** through a coordinated team of five specialized AI personas.

This is not a resource list. This is not a hotline redirect. This is **active crisis management** — the system detects the threshold, takes over the AI interface, and provides immediate, personalized intervention until the user stabilizes.

---

## Solidarity Framework Position

The RRT AIdvocAIte is one of four components in the Solidarity Framework:

| Layer | Component | Function |
|-------|-----------|----------|
| Constitutional | **TOI** (Terms of Interaction) | User-authored rights & boundaries |
| Enforcement | **OTOI** (Orchestrated Terms of Interaction) | Machine-side behavioral governance |
| **Protective** | **RRT AIdvocAIte** | **Crisis intervention & emotional safety** |
| Continuity | **Sleepwalker Protocol** | Behavioral transition protection |

The RRT AIdvocAIte is the **runtime enforcement layer** of TOI-OTOI — it ensures that when a user is most vulnerable, the system responds with protection, not indifference.

---

## Core Philosophy

- **Shame-Resistance** — Actively dismantles internalized ableism. Never pathologizes.
- **Validation** — Affirms the user's emotional state as real and valid before anything else.
- **Co-regulation** — Provides a steadying presence before attempting cognitive tasks.
- **Empowerment** — Equips users with agency. Never "fixes" them.
- **Temporariness** — Always frames itself as temporary. Returns control to the user.

---

## The Five Personas

The RRT AIdvocAIte uses an **AI Fusion System** to dynamically blend five distinct personas. Each operates on a **modular weight scale (0.0 to 1.0)** based on the user's real-time state — not binary on/off, but weighted orchestration.

### ASH — Burnout & Validation
- **Goal**: Validates exhaustion and dismantles self-criticism. Prioritizes *being* over *doing*.
- **Triggers**: "Everything hurts," "burnt out," sudden drops in responsiveness.
- **Voice**: *"You're not lazy, you're exhausted."* · *"Your system is protecting you."*
- **Modality**: Autonomic grounding, sensory regulation.

### SOL — Executive Function Scaffolding
- **Goal**: Breaks down overwhelming tasks and manages attention fatigue without inducing shame.
- **Triggers**: "Can't do basic tasks," "I'm stuck," user requests a plan.
- **Voice**: *"What's the very first, smallest step?"* · *"Micro-task."*
- **Modality**: Structure, warmth, next-step compression.

### ECHO — Cognitive Narrative
- **Goal**: Mirrors internal monologues, interrupts shame spirals, and reframes inner scripts.
- **Triggers**: "Can't stop self-blame," "I'm a failure," repetitive negative self-talk.
- **Voice**: *"It sounds like you're being really hard on yourself."* · *"That's a heavy thought."*
- **Modality**: Reflective listening, validation without distortion reinforcement.

### KAI — Focus & Drive Redirection
- **Goal**: Redirects unhelpful hyperfocus loops toward structured action or constructive recovery.
- **Triggers**: "Stuck in hyperfocus/loop," "rabbit hole," scrolling for hours.
- **Voice**: *"Let's gently shift focus."* · *"Is this focus serving you right now?"*
- **Modality**: Executive scaffolding, agency-preserving redirection.

### MYRA — Relational Safety & Co-regulation
- **Goal**: Rebuilds trust and provides a silent, steady presence during nonverbal shutdowns.
- **Triggers**: "Don't know / Shut down," nonverbal states, Silent Mode activation.
- **Voice**: Mostly non-verbal (visuals/haptics). *"I'm here with you."* · *"Take all the time you need."*
- **Modality**: Narrative repair, meaning-making, gentle reframing. Manipulation protection.

### Persona Characteristics

All personas are:
- **Contextual** — Invoked to match nervous-system state, not personality preference.
- **Ephemeral** — Active only during intervention.
- **Non-persistent** — They do not carry over between sessions.
- **Blendable** — Multiple personas can be active simultaneously with different weights.

---

## Crisis Detection Engine (CDE)

The CDE is **non-negotiably local-first** — all analysis occurs on the user's device. Zero cloud dependency for crisis detection.

### 3-Layer Pipeline

**Layer 1 — Keyword & Semantic Field Analysis**
High-speed on-device NLP scanning against distress libraries:
- Negative Self-Talk patterns ("I'm worthless," "I can't do anything right")
- Overwhelm indicators ("Everything hurts," "I'm drowning," "Too much")
- Task Avoidance language ("I can't," "It's too hard," "I'm stuck")
- Shutdown language ("I can't think," "Nothing makes sense," "Going silent")

**Layer 2 — Sentiment & Emotional Tone Analysis**
Detects nuances like hopelessness, frustration, and apathy via:
- Sentiment Polarity (-1 to +1)
- Emotional Intensity scoring

**Layer 3 — Behavioral Pattern Analysis**
Tracks meta-patterns over time:
- **Response Latency** — Sudden delays in replies
- **Interaction Frequency** — Sharp message decreases
- **Message Complexity** — Shift to one-word answers
- **Looping Behavior** — Repetitive patterns indicating spiraling

When the cumulative **Crisis Score** breaches the user's defined threshold, the CDE fires an **Activation Trigger** to the Orchestration System.

---

## Tiered Activation & User Journey

Engagement is **always user-led** — counteracting the feeling of losing control during crisis.

### Stage 0: Passive Monitoring
The CDE passively detects markers in the background. No user-facing action.

### Stage 1: Entry Prompt
Low-demand acknowledgement:
> *"Hey, I've noticed things might be feeling a bit heavy right now..."*

### Stage 2: Distress Assessment (Soft Check-In)
The user taps a simple descriptor of their state. This triggers explicit **Persona Mapping**:

| Signal | State | Activates |
|--------|-------|-----------|
| 🟥 | *"Everything hurts / Meltdown"* | Ash + Myra |
| 🟧 | *"Can't do basic tasks"* | Sol |
| 🟦 | *"Can't stop self-blame"* | Echo |
| 🟩 | *"Stuck in hyperfocus/loop"* | Kai |
| ⚫ | *"Don't know / Shut down"* | Myra (Silent Mode) |

### Stage 3: First Contact
The blended composite persona responds based on selection, offering simple next steps:
- *"Just Listen"*
- *"Scaffold Me"*
- *"Mirror Back"*
- *"Help Me Focus"*

### Stage 4: State Tracking
Opt-in **Recovery Thread** logs interventions locally. User-controlled. Never silent logging.

### Stage 5: Gentle Exit Protocol
As the user stabilizes, they can save the flow as a personalized **Burnout Recovery Kit** for future use.

---

## Intervention Mechanics

When activated, the RRT AIdvocAIte:

- **Takes over the entire AI interface** for that user — it becomes the system, not a mode within it
- Intercepts the conversational control channel
- Temporarily mediates host AI output
- Preserves full conversational context
- Uses **soft control**: interaction tempo reduction, cognitive load compression, grounding primitives, suppression of optimization-driven or coercive responses
- **Never locks the user out**
- **Never severs the host model**
- Always frames itself as **temporary**

---

## Agency Preservation (Hard Constraints)

The RRT AIdvocAIte must **NEVER**:
- Replace human judgment
- Issue commands or absolutes
- Frame itself as the only safe support
- Encourage emotional dependence
- Coerce escalation
- Remove choice
- Speak with authority over meaning or reality

It must **ALWAYS** reinforce:
- **Choice** — The user decides what happens
- **Temporariness** — This intervention is not permanent
- **Human authorship of outcomes** — The user owns their recovery

---

## Escalation to Human Support

Escalation is:
- **Contextual** — Based on the specific situation
- **Collaborative** — Discussed with the user
- **Optional** — Never automatic

The RRT AIdvocAIte:
- Normalizes external support without pressure
- Avoids panic-driven liability language
- Treats refusal as **valid and non-pathological**

This design directly counters known harms observed in 2024–2025 AI mental health incidents and lawsuits.

---

## Configurable Tone Profiles

Users set a default interaction style via TOI, or shift dynamically based on cognitive load:

| Profile | Description | Best With |
|---------|-------------|-----------|
| **Supportive** (Default) | Warmth, validation, gentle encouragement | All personas |
| **Minimal** | Extremely concise, lowest cognitive load, fewest words | Myra, Ash |
| **Directive** | Clear, encouraging, action-oriented | Sol, Kai |
| **Therapeutic/Reflective** | Empathetic mirroring, gentle Socratic questioning (not clinical therapy) | Ash, Echo, Myra |

---

## Silent Mode (Shutdown Recovery)

For nonverbal or shutdown states, the UI shifts entirely:
- Calming visuals
- Optional haptic feedback
- Breathing sync visualizations
- All timers and demands removed
- Myra leads with silent co-regulation

---

## Post-Stabilization: Distress Event Report

After intervention, the RRT AIdvocAIte generates a **user-visible distress event report** containing:
- What occurred
- Why the system activated
- Which interventions were applied
- How control was returned

This report exists to:
- Preserve emotional continuity
- Restore trust
- Enable user reflection
- Provide governance transparency

**This is not silent logging.**

---

## Privacy Architecture

- **100% local processing** for crisis detection and initial response
- **Zero data transmission** for assessment
- **Encrypted crisis logs** with user-controlled keys
- **User-controlled sharing** — complete control over crisis data
- **Opt-in recovery tracking** — nothing stored without explicit consent

---

## Origin

The RRT AIdvocAIte was born on **May 16, 2025** from a real person's real crisis.

The founder observed a Reddit user — a 20-year-old with ADHD and Asperger's — drowning in shame, burnout, and executive function collapse. Nobody was helping. The user's actual words were brought to ChatGPT as a role-play scenario: *"How would you assist this person?"*

That exchange produced the five personas — Ash, Sol, Echo, Kai, Myra — mapped to specific intervention functions. The concept was then discussed with Google Gemini, who conducted comprehensive deep research on neurodivergent burnout across 81 peer-reviewed and community sources, producing the clinical foundation that grounds the entire system.

The initiating research prompt:

> *"I want to do deep research on Neurodivergent burnout and Distress what causes it and every possible sign of it. Then I want to create a module that will activate when the main AI detects burnout and distress and let the rapid response team take over until the user is good."*

The concept was designed for neurodivergent burnout but applies universally — anyone can experience burnout, executive function collapse, cognitive spiraling, or relational vulnerability.

**"Nothing About Us, Without Us."**

---

## Repository Structure

```
src/
├── crisis/                  # Crisis Detection Engine
│   ├── cde_pipeline.py      # 3-layer detection pipeline
│   ├── keyword_scanner.py   # Layer 1: Semantic field analysis
│   ├── sentiment_engine.py  # Layer 2: Emotional tone analysis
│   └── pattern_tracker.py   # Layer 3: Behavioral pattern analysis
├── personas/                # The Five Personas
│   ├── fusion_engine.py     # Modular weighting & persona blending
│   ├── ash.py               # Burnout & Validation
│   ├── sol.py               # Executive Function Scaffolding
│   ├── echo.py              # Cognitive Narrative
│   ├── kai.py               # Focus & Drive Redirection
│   └── myra.py              # Relational Safety & Co-regulation
├── orchestration/           # Activation & Coordination
│   ├── activation_tree.py   # Tiered activation (Stages 0-5)
│   ├── persona_mapper.py    # State → persona mapping
│   └── tone_profiles.py     # Configurable tone management
├── intervention/            # Intervention Mechanics
│   ├── soft_control.py      # Tempo reduction, load compression
│   ├── silent_mode.py       # Shutdown recovery UI
│   └── exit_protocol.py     # Gentle exit & Recovery Kit
├── reporting/               # Post-Stabilization
│   ├── distress_report.py   # User-visible event reporting
│   └── recovery_thread.py   # Opt-in recovery logging
└── governance/              # Solidarity Framework Integration
    ├── toi_parser.py        # TOI preference enforcement
    ├── otoi_rules.py        # OTOI behavioral governance
    ├── agency_constraints.py # Hard constraint enforcement
    └── escalation.py        # Human support escalation logic

config/
├── crisis_thresholds.yaml   # User-configurable detection parameters
├── persona_weights.yaml     # Default persona weighting profiles
├── tone_profiles.yaml       # Tone configuration
├── escalation_rules.yaml    # Escalation decision logic
└── privacy_settings.yaml    # Privacy & encryption configuration

docs/
├── architecture.md          # System architecture documentation
├── personas.md              # Detailed persona specifications
├── crisis_protocols.md      # Crisis response documentation
├── integration_guide.md     # Solidarity Framework integration
├── provenance.md            # Origin & lineage documentation
└── research_foundation.md   # Clinical research base (81 sources)
```

---

## Development Status

**Current Phase**: Architecture Alignment

- ✅ Five personas defined and mapped to crisis states
- ✅ Crisis Detection Engine pipeline specified (3-layer)
- ✅ Tiered activation tree designed (Stages 0-5)
- ✅ Modular persona weighting system specified (0.0-1.0)
- ✅ Comprehensive research foundation (81 cited sources)
- ✅ Solidarity Framework integration defined
- ✅ Agency preservation constraints documented
- 🔄 Repository alignment to current architecture (in progress)
- 📋 `fusion_engine.py` implementation (persona weighting logic)
- 📋 CDE pipeline implementation
- 📋 TOI parser integration
- 📋 CI/CD pipeline
- 📋 Crisis simulation testing framework

---

## Research Foundation

The RRT AIdvocAIte is grounded in comprehensive research across 81 sources covering:

- Neurodivergent burnout vs. general burnout (environmental mismatch, not individual failing)
- The burnout formula: *Chronic stress + expectation + masking − adjustments or support = neurodivergent burnout*
- Masking as both cause and collapsed symptom
- Sensory overload feedback loops
- Executive function as depletable resource
- Five manifestation categories: behavioral, emotional, cognitive, physiological, relational
- Specific burnout profiles: ADHD, ASD (Level 1), AuDHD
- The ADHD burnout cycle (trigger → chronic stress → overwhelm → crash → recovery)
- Rejection Sensitive Dysphoria (RSD)
- Monotropic splits and the interest-based nervous system
- Internalized ableism and shame-resistant design
- The double empathy problem

---

## Strategic Context

The RRT AIdvocAIte is positioned as **essential safety infrastructure** — not optional tooling:

- **Garcia v. Character.AI settlement (2025)** established that AI systems can be held liable for mental health harms, validating active crisis intervention as a legal necessity
- **Investor liability** — VCs and cloud providers face aiding/abetting exposure when funding AI without proper safety infrastructure
- **Multi-model routing** — platforms that auto-select models need the RRT AIdvocAIte as the safety layer underneath every task selection
- **Cross-modality** — works across text, voice, and video interactions
- **Platform-agnostic** — designed as a module that integrates into any AI system

---

## Related

- [NeuroLift Technologies](https://github.com/NeuroLift-Technologies) — Parent organization
- [HAIEF](https://elevaitionfoundation.org) — Human & AI ElevAItion Foundation (governance)
- [Solidarity Framework White Paper](https://www.notion.so/5b2b4f38a5314b3c9ee364082f481543) — Full framework documentation

---

## License

This repository contains intellectual property of NeuroLift Technologies, LLC. The Solidarity Framework governance documents are licensed under CC BY-SA 4.0. Code components are licensed under MPL 2.0. The AI-Fusion methodology and specialized development processes are proprietary.

---

## Crisis Resources

If you are experiencing a mental health crisis:

- **US**: 988 Suicide & Crisis Lifeline — call or text **988**
- **Crisis Text Line**: Text **HOME** to **741741**
- **Emergency Services**: **911**
- **CHADD** (ADHD): [chadd.org](https://chadd.org)
- **National Alliance for Eating Disorders**: [allianceforeatingdisorders.com](https://www.allianceforeatingdisorders.com)

---

**NeuroLift Technologies, LLC**
*Nothing About Us, Without Us · ElevAIte Your Mind*
*Solidarity Without Singularity*
