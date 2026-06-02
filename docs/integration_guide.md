# NeuroLift Ecosystem Integration Guide

This guide documents the **current, code-verified integration surface** for this repository.
It intentionally avoids speculative architecture and focuses on behavior implemented in:

- `src/rrt_advocate.py`
- `config/crisis_thresholds.yaml`
- `config/personas.yaml`
- `config/toi_defaults.yaml`
- `config/tone_profiles.yaml`

> Safety-critical note: this repository is governed by ORG-DEV-OTOI-1.0.2. Do not modify crisis logic or thresholds without explicit approval.

---

## 1) What this repository currently provides

`RRTAdvocate` is an async orchestration layer that:

1. Processes user messages through a local-first crisis detection pipeline.
2. Enforces Terms of Interaction (TOI) consent before full RRT deployment.
3. Routes user choices through the Stage 0-5 dialogue tree.
4. Blends Ash/Sol/Echo/Kai/Myra responses through the persona fusion engine.
5. Filters outputs through OTOI middleware and exposes operator lifecycle hooks.

The core implementation is in `src/rrt_advocate.py`.

---

## 2) Public interfaces (codepaths you can integrate with)

### Enums

- `CrisisLevel`: `GREEN`, `YELLOW`, `ORANGE`, `RED`, `BLACK`
- `ResponseStatus`: `PENDING`, `ACTIVE`, `SUCCESSFUL`, `ESCALATED`, `FAILED`

### Data models

- `CrisisAssessment`
  - Includes `crisis_level`, `confidence_score`, `user_safety_score`,
    `recommended_interventions`, and `context_factors`.
- `InterventionResponse`
  - Tracks intervention lifecycle (`start_time`, `end_time`, `status`, `effectiveness_score`).
- `TOIConfig`
  - Controls `tone_profile`, `pacing`, `silent_mode_preferred`,
    `allow_timers`, `allow_task_loops`, preferred/excluded personas, and consent state.

### Main class

- `RRTAdvocate(user_id: str, config_path: str = "config/crisis_thresholds.yaml", toi_config: Optional[TOIConfig] = None, supervisor_interface: Optional[SupervisorInterface] = None)`
- `await process_message(user_message: str) -> Dict[str, Any]`
- `await select_stage_option(option_key: str, free_text: Optional[str] = None) -> Dict[str, Any]`
- `await start_monitoring() -> bool`
- `await stop_monitoring() -> bool`
- `await assess_current_state(message: str = "") -> CrisisAssessment`
- `await get_status_report() -> Dict[str, Any]`
- `await manual_intervention(intervention_type: str, context: Optional[Dict[str, Any]] = None) -> bool`
- `await shutdown()`

### Helpers

- `await create_rrt_advocate(...) -> RRTAdvocate`
  - Creates and returns an initialized instance. It does **not** perform an initial assessment.
- `create_toi_config(...) -> TOIConfig`
  - Builds a TOI configuration with supported tone profiles:
    `supportive_default`, `minimal`, `directive`, `therapeutic_reflective`.

---

## 3) Runtime workflows

### Primary conversational workflow

The main user-facing path is `process_message()`:

1. `crisis_detector.detect_crisis_indicators(user_message)` runs the local
   3-layer CDE: keyword, sentiment, and behavioral analysis.
2. `crisis_assessor.assess_crisis(indicators)` maps aggregate confidence to
   `GREEN`/`YELLOW`/`ORANGE`/`RED`/`BLACK`.
3. If TOI consent has not been granted, the response is Stage 1 entry/consent
   and includes `requires_consent=True`.
   - Source-ordering caveat: this consent gate currently runs before the
     self-harm emergency branch. A pre-consent self-harm indicator can therefore
     return the consent prompt with an emergency crisis level rather than the
     emergency resource payload.
4. After consent is already granted, self-harm risk triggers
   `_emergency_escalation()` and returns emergency crisis resources.
5. Non-green assessments call `_handle_crisis(assessment)`.
6. The dialogue tree processes free text and returns a unified response with
   `response_text`, `stage`, options, crisis level, confidence, and response time.

Stage option selections are handled separately:

```python
response = await advocate.select_stage_option("yes")
response = await advocate.select_stage_option("meltdown")
```

### Background monitoring workflow

The monitoring path remains available for service-style integrations:

1. `start_monitoring()` sets `is_monitoring=True` and starts `_monitoring_loop()` as a background task.
2. `_monitoring_loop()`:
   - calls `assess_current_state()`
   - if level is not `GREEN`, calls `_handle_crisis(assessment)`
   - updates pattern analysis via `pattern_analyzer.update_patterns(assessment)`
3. `_handle_crisis()` routes by severity:
   - `YELLOW`/`ORANGE` -> `_deploy_standard_interventions()`
   - `RED` -> `_deploy_intensive_interventions()`
   - `BLACK` or low `user_safety_score` -> `_emergency_escalation()`
4. Supervisor callbacks fire when configured:
   - `notify_advocate_status(...)` on start/stop
   - `handle_crisis(...)` for detected crises
   - `emergency_escalation(...)` for emergency states
5. `shutdown()` stops monitoring, persists patterns (`save_patterns()`), and logs final status.

---

## 4) Internal components and integration points

The orchestration layer imports these in-repo modules from `src/`:

- `crisis.detectors.crisis_detector.CrisisDetector`
- `crisis.assessors.crisis_assessor.CrisisAssessor`
- `response.interventions.intervention_manager.InterventionManager`
- `response.de_escalation.de_escalation_engine.DeEscalationEngine`
- `coordination.supervisor.supervisor_interface.SupervisorInterface`
- `learning.patterns.pattern_analyzer.PatternAnalyzer`

`src/rrt_advocate.py` inserts `src/` onto `sys.path` for direct execution, so run
developer commands from the repository root unless your integration packages the
modules differently.

Minimal supervisor contract expected by `RRTAdvocate`:

```python
class SupervisorInterface:
    async def notify_advocate_status(self, advocate_id: str, status: str, user_id: str): ...
    async def handle_crisis(self, advocate_id: str, crisis_assessment, user_id: str): ...
    async def emergency_escalation(self, advocate_id: str, crisis_assessment, user_id: str): ...
```

---

## 5) Configuration runbook (`config/`)

The default crisis config path is `config/crisis_thresholds.yaml`. It contains:

- crisis level ranges (`green`..`black`)
- indicator weights and thresholds
- crisis pattern definitions
- escalation rules
- intervention mappings by severity
- privacy/security/performance parameters

Additional source-verified config files:

- `config/personas.yaml` defines the five personas, activation signals, prompt
  prefixes, and template responses.
- `config/toi_defaults.yaml` defines default TOI values, consent prompt text,
  pacing intervals, and scaffolding rules.
- `config/tone_profiles.yaml` defines tone profile descriptions, token budgets,
  prompt directives, sentence starters, and forbidden phrases.

Important operational constraints:

- `RRTAdvocate._monitoring_loop()` currently sleeps for a fixed `1` second interval.
  - It does **not** currently consume per-level `monitoring_interval` values from YAML.
- Escalation behavior in code is driven by `assessment.user_safety_score` and `assessment.crisis_level`.
  - `RRTAdvocate` directly checks `user_safety_score < 0.3` and `BLACK` crisis level.
  - `CrisisAssessor` returns hard-coded per-level `escalation_threshold` values.
  - YAML `escalation_rules` are present in config but are not currently wired into these runtime checks.
- `PatternAnalyzer.save_patterns()` writes local aggregate metrics to `data/patterns/{user_id}_patterns.json`.
  Raw message text is not stored by `PatternAnalyzer`.

---

## 6) Developer setup (current repository state)

### Prerequisites

- Python 3.10+
- Runtime dependency for YAML parsing: `PyYAML`

### Suggested local workflow

1. Create and activate a virtual environment.
2. Install local developer dependencies:

```bash
python3 -m pip install -U pip pytest pytest-asyncio pyyaml
```

3. Run a basic import check from the repo root:

```bash
python3 -c "from src.rrt_advocate import RRTAdvocate; print('import ok')"
```

4. Run the demo/smoke path:

```bash
python3 src/rrt_advocate.py
```

5. Run tests:

```bash
python3 -m pytest tests/test_cde.py tests/test_dialogue_tree.py tests/test_fusion_engine.py tests/test_toi.py
```

Full `python3 -m pytest` currently also collects `tests/test_rrt_advocate.py`.
That file is a legacy stub harness that injects fake `crisis.*` modules and does
not provide the current `CrisisIndicators` API, so it fails during import before
exercising `RRTAdvocate`. Keep full-suite failures from that file separate from
component-suite regressions until the harness is updated.

---

## 7) Troubleshooting and common pitfalls

### `ModuleNotFoundError` for `crisis.*`, `response.*`, `coordination.*`, or `learning.*`

Cause: the command is not running with the repo's `src/` modules importable.

Fix: run from the repository root, use `python3 src/rrt_advocate.py` for the demo
path, or add `/path/to/rrt-advocate/src` to `PYTHONPATH` in your integration.

### `python: command not found`

Cause: some Linux images expose Python as `python3` only.

Fix: use `python3` in local commands, or create a shell alias only in your local environment.

### Full pytest fails in `tests/test_rrt_advocate.py`

Cause: `tests/test_rrt_advocate.py` installs legacy stub modules into `sys.modules`.
Those stubs predate the vendored `src/crisis/` implementation and do not expose
`CrisisIndicators`.

Fix: use the focused component-suite command from Section 6 for current green
validation, and update the legacy harness before treating full-suite failures as
runtime regressions.

### `ModuleNotFoundError: No module named 'yaml'`

Cause: `src/crisis/assessors/crisis_assessor.py` loads `config/crisis_thresholds.yaml`
with `yaml.safe_load`.

Fix: install `PyYAML` in the active environment.

### First conversational response keeps asking for consent

Cause: `TOIConfig.consent_given` defaults to `False`; Stage 1 consent is required
before full RRT deployment.

Fix: route the user's choice through `select_stage_option("yes")`, or construct a
TOI config with consent already granted only when your product flow has collected
explicit consent.

### Duplicate log lines after creating multiple `RRTAdvocate` instances

Cause: `_setup_logging()` always adds a new `StreamHandler` to the same logger name for a given `user_id`.

Fix: guard handler registration in your fork/integration layer or reuse advocate instances per user.

### Monitoring appears active after caller scope exits

Cause: `start_monitoring()` launches `_monitoring_loop()` as a background task via `asyncio.create_task`.

Fix: always call `await shutdown()` (or at minimum `await stop_monitoring()`) in service teardown paths.

### `intervention_success_rate` remains low/zero unexpectedly

Cause: success-rate updates are calculated from `active_interventions` entries with completion data; completed interventions are then removed from that list.

Fix: if this metric is operationally important, persist completed interventions in integration code or adjust implementation before relying on it for dashboards/alerts.

---

## 8) Operational runbook for service owners

### Start sequence

1. Instantiate via `create_rrt_advocate(...)` (per user session).
2. Call `start_monitoring()`.
3. Verify `monitoring_active` via `get_status_report()`.

### During runtime

- Poll or request `get_status_report()` for:
  - TOI config and consent status
  - dialogue stage/session summary
  - current crisis level/confidence
  - active intervention count
  - response performance metrics
- Use `manual_intervention(...)` for operator-assisted recovery workflows.

### Stop sequence

1. Call `shutdown()`.
2. Confirm monitoring is inactive and final status has been logged.

---

## 9) Known documentation boundaries

This guide intentionally documents only behavior verifiable in this repository.
For roadmap plans, ecosystem proposals, or architectural intent not yet implemented here, treat those artifacts as design references rather than runtime truth.
