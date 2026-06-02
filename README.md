# RRT AIdvocAIte

**Real-Time Crisis Intervention & Protective Layer — Solidarity Framework**

> *"When burnout hits, the cavalry arrives."*

---


## Local Development (Repository Snapshot)

The core runtime modules live under `src/` and are importable either through
`src.rrt_advocate` or by putting `src` on `PYTHONPATH` for top-level imports such
as `crisis.detectors.crisis_detector`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip pytest pytest-asyncio PyYAML
# Optional: improves local sentiment scoring; otherwise a heuristic fallback is used.
pip install vaderSentiment
pytest
```

Useful focused checks:

```bash
pytest tests/test_cde.py
pytest tests/test_rrt_advocate.py
PYTHONPATH=src python -c "from crisis.detectors.crisis_detector import CrisisDetector; print('cde import ok')"
```

Project tooling defaults are defined in `pyproject.toml`. See
`docs/integration_guide.md` for the code-verified integration surface and
operational runbook.

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
- Task Avoidance language ("I can't," "It's too hard," "I'm stuck")
- Overwhelm indicators ("Everything hurts," "I'm drowning," "Too much")
- Meltdown language ("meltdown," "falling apart," "can't stop panicking")
- Shutdown language ("I can't think," "Nothing makes sense," "Going silent")
- Hyperfocus loop language ("rabbit hole," "looping," "can't stop focusing")
- Self-harm risk language, which forces maximum detector confidence and
  emergency escalation handling

**Layer 2 — Sentiment & Emotional Tone Analysis**
Tracks emotional polarity over a sliding window:
- Uses `vaderSentiment` locally when installed
- Falls back to a local heuristic lexicon when VADER is absent
- Emits the fallback notice lazily at layer instantiation, not at import time
- Classifies trends as `stable`, `declining`, `sharply_declining`, or `recovering`

**Layer 3 — Behavioral Pattern Analysis**
Tracks session-level metadata over time:
- **Response Latency** — long gaps between messages
- **Message Complexity** — shifts toward very short or fragmented messages
- **Looping Behavior** — repeated word-overlap patterns indicating spiraling
- **Privacy Constraint** — stores timestamps, counts, punctuation density, and
  non-reversible hashed word tokens; it does not store raw message content

`CrisisDetector` aggregates the layers with source-defined weights
(`keyword=0.45`, `sentiment=0.35`, `behavioral=0.20`) and returns
`CrisisIndicators`. `CrisisAssessor` then maps aggregate confidence to crisis
levels and recommended interventions. `config/crisis_thresholds.yaml` is loaded
by the assessor for intervention mapping, but detector patterns, layer weights,
and sensitivity thresholds are defined in code and must not be changed without
explicit approval.

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

- **100% local CDE processing** — detector layers make no external API calls.
- **No supervisor transmission by default** — `LocalSupervisor` logs locally when
  no custom supervisor is supplied.
- **Behavioral metadata only** — Layer 3 stores timing/count metrics and hashed
  word tokens for looping detection, not raw message text.
- **Local pattern storage** — `PatternAnalyzer` persists aggregate metrics to
  `data/patterns/{user_id}_patterns.json` when `shutdown()` calls
  `save_patterns()`. Encryption is not implemented in this repository snapshot.
- **Integration responsibility** — host applications must not persist or export
  `CrisisIndicators.raw_text`, crisis assessments, or pattern files without
  explicit user consent and an approved storage design.

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
├── rrt_advocate.py                         # Main async orchestration entry point
├── crisis/
│   ├── detectors/
│   │   ├── crisis_detector.py              # 3-layer CDE aggregator
│   │   ├── keyword_layer.py                # Layer 1: semantic fields
│   │   ├── sentiment_layer.py              # Layer 2: local sentiment trends
│   │   └── behavioral_layer.py             # Layer 3: privacy-preserving metadata
│   └── assessors/
│       └── crisis_assessor.py              # Indicators -> crisis level/interventions
├── dialogue/
│   ├── dialogue_tree.py                    # Stage 0-5 dialogue state machine
│   └── stages.py                           # Stage configuration and options
├── personas/
│   ├── fusion_engine.py                    # Modular weighting & persona blending
│   ├── ash.py / sol.py / echo.py / kai.py / myra.py
│   └── base_persona.py
├── response/
│   ├── interventions/intervention_manager.py
│   └── de_escalation/de_escalation_engine.py
├── coordination/supervisor/
│   └── supervisor_interface.py             # Local/default supervisor contract
├── learning/patterns/
│   └── pattern_analyzer.py                 # Local aggregate pattern storage
└── toi/
    ├── toi_models.py
    ├── toi_parser.py
    └── otoi_middleware.py

config/
└── crisis_thresholds.yaml                   # Assessor/intervention configuration

docs/
├── integration_guide.md                    # Code-verified integration/runbook
├── active-threads.md                       # Agent coordination state
├── agent-log/                              # Agent registration/handoff records
└── escalations/                            # Escalation records
```

---

## Development Status

**Current Phase**: Source implementation alignment

- ✅ Five personas implemented under `src/personas/`
- ✅ Crisis Detection Engine pipeline implemented under `src/crisis/detectors/`
- ✅ Tiered dialogue tree implemented under `src/dialogue/`
- ✅ Modular persona weighting implemented in `src/personas/fusion_engine.py`
- ✅ TOI parser and OTOI middleware implemented under `src/toi/`
- ✅ Local supervisor, intervention, de-escalation, and pattern modules present
- ✅ Solidarity Framework integration and agency constraints documented
- 🔄 Packaging/dependency declarations are still being aligned with runtime imports
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
