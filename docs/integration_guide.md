# NeuroLift Ecosystem Integration Guide

This guide documents the **current, code-verified integration surface** for this
repository. It intentionally avoids speculative architecture and focuses on
behavior implemented in source.

> Safety-critical note: this repository is governed by ORG-DEV-OTOI-1.0.2. Do
> not modify crisis logic, crisis thresholds, persona blending, or safety
> response text without explicit approval from Joshua W. Dorsey, Sr.

---

## 1) Runtime surfaces

| Surface | Source | Integration purpose | Local-first? |
|---|---|---|---|
| Python protective layer | `src/rrt_advocate.py` plus `src/crisis/`, `src/toi/`, `src/dialogue/`, `src/personas/`, `src/response/`, `src/coordination/`, `src/learning/` | Full TOI/OTOI, dialogue-tree, persona-fusion, intervention, monitoring, status, and shutdown orchestration. | Yes |
| TypeScript CDE package | `packages/rrt-advocate/` | npm package for detection and assessment only via `CrisisEngine`, `CrisisDetector`, and `CrisisAssessor`. | Yes |
| Cloudflare Worker assistant | root `package.json`, `wrangler.jsonc`, `src/index.ts`, `public/` | Hosted chat UI/API using Workers AI and a lightweight route-local distress pre-check. | No; model responses use Workers AI |

Use the Python protective layer when an integration needs the full RRT response
workflow. Use the TypeScript package when an integration only needs local crisis
detection/assessment. Use the Worker for the hosted browser assistant described
in [`docs/rrt-aidvocaite-worker.md`](rrt-aidvocaite-worker.md).

---

## 2) Python public interfaces

### Main class and factories

```python
from src.rrt_advocate import RRTAdvocate, create_rrt_advocate, create_toi_config

toi = create_toi_config(tone_profile="supportive_default", pacing="slow")
advocate = await create_rrt_advocate("user-123", toi_config=toi)
```

`RRTAdvocate(...)` accepts:

- `user_id`
- `config_path="config/crisis_thresholds.yaml"`
- optional `toi_config`
- optional `supervisor_interface`

Primary methods:

| Method | Purpose |
|---|---|
| `await process_message(user_message)` | Runs CDE analysis, checks TOI consent, routes through the dialogue tree and persona fusion, then returns response/stage/crisis metadata. |
| `await select_stage_option(option_key, free_text=None)` | Advances the Stage 0-5 dialogue tree from a user option. |
| `await assess_current_state(message="")` | Runs crisis detection and assessment for an optional message. |
| `await start_monitoring()` / `await stop_monitoring()` | Starts or stops the background one-second monitoring loop. |
| `await manual_intervention(intervention_type, context=None)` | Calls the intervention manager with `urgency_level="manual"`. |
| `await get_status_report()` | Returns TOI config, current crisis state, dialogue summary, OTOI summary, active intervention count, performance, and pattern summary. |
| `await shutdown()` | Stops monitoring, saves patterns, logs final status, and completes shutdown. |

### Conversation flow

`process_message(...)` follows this path:

1. `CrisisDetector.detect_crisis_indicators(...)`
2. `CrisisAssessor.assess_crisis(...)`
3. Stage 1 consent gate via `OTOIMiddleware.check_consent()`
4. Immediate emergency response when `indicators.self_harm_risk` is true
5. Crisis handling for non-`GREEN` assessments
6. `DialogueTree.process_free_text(...)`
7. Persona-fusion/OTOI-filtered response metadata

`select_stage_option(...)` delegates to the dialogue tree. Implemented stage
option keys include `yes`, `not_now`, `silent`, `meltdown`, `cant_task`,
`self_blame`, `hyperfocus`, `shutdown`, `skip`, `helped`, `more`, `stay`,
`done`, `better`, `same`, `worse`, and `goodbye`.

### Supervisor callbacks

Pass a `SupervisorInterface` implementation when a host service needs lifecycle
or escalation hooks:

```python
class SupervisorInterface:
    async def notify_advocate_status(self, advocate_id: str, status: str, user_id: str): ...
    async def handle_crisis(self, advocate_id: str, crisis_assessment, user_id: str): ...
    async def emergency_escalation(self, advocate_id: str, crisis_assessment, user_id: str): ...
```

If omitted, `LocalSupervisor` logs status/crisis events locally.

---

## 3) TypeScript CDE package interface

The package under `packages/rrt-advocate/` is named
`@neurolift-technologies/rrt-advocate` and requires Node 20+.

```ts
import { CrisisEngine, CrisisLevel } from "@neurolift-technologies/rrt-advocate";

const engine = new CrisisEngine("user-123");
const assessment = await engine.assess("I can't cope, everything is too much");

if (assessment.crisisLevel !== CrisisLevel.GREEN) {
  // Route to appropriate support in the host application.
}
```

Package scope boundaries:

- Ports detection and assessment only.
- Exports lower-level `KeywordLayer`, `SentimentLayer`, `BehavioralLayer`,
  `CrisisDetector`, and `CrisisAssessor`.
- Uses a vendored `config/crisis_thresholds.yaml` that must stay synced with the
  root canonical thresholds file.
- Documents one intentional Layer 1 divergence in
  `packages/rrt-advocate/KNOWN_LIMITATIONS.md`: apostrophe-insensitive matching
  fails open for dictated/smart-quote input.

---

## 4) Cloudflare Worker assistant interface

The root Worker serves:

- static UI routes from `public/`
- `GET /api/health`
- `POST /api/chat`

`/api/chat` keeps valid recent chat messages, truncates each message to 4,000
characters, keeps the latest 16 messages, replaces caller-supplied system
messages, streams a Workers AI response, and sets `x-rrt-risk-level` to
`stable`, `elevated`, `high`, or `critical`.

See [`docs/rrt-aidvocaite-worker.md`](rrt-aidvocaite-worker.md) for curl
examples, Wrangler commands, auth pitfalls, and deployment guardrails.

---

## 5) Configuration runbook

| File | Runtime role | Guardrail |
|---|---|---|
| `config/crisis_thresholds.yaml` | Canonical Python CDE levels, layer weights, crisis patterns, intervention mappings, privacy/performance settings. | Safety-critical; do not edit without escalation. |
| `packages/rrt-advocate/config/crisis_thresholds.yaml` | Vendored package copy of the canonical thresholds. | Must stay synced; threshold changes require escalation. |
| `config/toi_defaults.yaml` | Default Terms of Interaction, consent prompt, pacing intervals, scaffolding rules. | Preserve agency-first defaults. |
| `config/personas.yaml` | Persona roles, activation signals, prompts, and template responses. | Persona routing/blending changes require escalation. |
| `config/tone_profiles.yaml` | Tone directives, max token guidance, sentence starters, forbidden phrases. | Avoid shame-inducing or coercive phrasing. |

Operational constraints verified in source:

- `RRTAdvocate._monitoring_loop()` sleeps for a fixed one-second interval and
  does not currently consume YAML `monitoring_interval` values directly.
- `RRTAdvocate` triggers emergency escalation when `user_safety_score < 0.3`,
  `crisis_level == BLACK`, or `indicators.self_harm_risk` is true.
- `create_toi_config(...)` always sets `allow_task_loops` to `False`.

---

## 6) Developer setup

### Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip pyyaml pytest pytest-asyncio
pytest
python3 src/rrt_advocate.py
```

### TypeScript CDE package

```bash
cd packages/rrt-advocate
npm install
npm run build
npm test
```

### Worker assistant

```bash
npm install
npm run check
npm run dev
```

`npm run deploy` publishes the Worker and requires explicit human approval under
OTOI. In unauthenticated cloud environments, `npm run dev` may open Wrangler
OAuth; use the Worker runbook's local-mode `/api/health` smoke test when model
responses cannot be exercised.

---

## 7) Troubleshooting and common pitfalls

### `ModuleNotFoundError: No module named 'yaml'`

Cause: `src/toi/toi_parser.py` imports PyYAML, but `pyproject.toml` currently
does not declare runtime dependencies.

Fix: install `pyyaml` in the local environment before running Python demos or
tests.

### Duplicate log lines after creating multiple `RRTAdvocate` instances

Cause: `_setup_logging()` adds a new `StreamHandler` to the logger for the
`user_id`.

Fix: reuse advocate instances per user or guard handler registration in the host
integration.

### Monitoring remains active after caller scope exits

Cause: `start_monitoring()` launches `_monitoring_loop()` via
`asyncio.create_task`.

Fix: always call `await shutdown()` or `await stop_monitoring()` in teardown.

### `intervention_success_rate` remains low or zero

Cause: success-rate updates are calculated from `active_interventions` entries
with completion data, and completed interventions are removed from that list.

Fix: persist completed intervention outcomes in integration code before using
this value for dashboards or alerts.

### Worker `/api/chat` cannot be tested locally

Cause: normal Wrangler development uses remote Workers AI and requires
Cloudflare authentication with Workers AI access.

Fix: verify `/api/health` with local mode, then run authenticated
`npm run dev` before testing streamed model responses.

---

## 8) Known documentation boundaries

This guide documents behavior verifiable in this repository. Treat broader
host-interface takeover, rich Silent Mode UI, Burnout Recovery Kit creation, and
post-stabilization report generation as product/host-application intent unless
the host application implements those experiences around the current Python or
Worker surfaces.
