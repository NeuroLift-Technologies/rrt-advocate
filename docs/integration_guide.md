# NeuroLift Ecosystem Integration Guide

This guide documents the **current, code-verified integration surface** for this repository.
It intentionally avoids speculative architecture and focuses on behavior implemented in:

- `src/rrt_advocate.py`
- `config/crisis_thresholds.yaml`

> Safety-critical note: this repository is governed by ORG-DEV-OTOI-1.0.0. Do not modify crisis logic or thresholds without explicit approval.

---

## 1) What this repository currently provides

`RRTAdvocate` is an async orchestration layer that:

1. Runs continuous crisis assessments in a monitoring loop.
2. Routes non-green assessments into tiered intervention flows.
3. Escalates emergencies to a supervisor interface (if provided).
4. Exposes status/reporting and manual intervention hooks for operators.

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

### Main class

- `RRTAdvocate(user_id: str, config_path: str = "config/crisis_thresholds.yaml", supervisor_interface: Optional[SupervisorInterface] = None)`
- `await start_monitoring() -> bool`
- `await stop_monitoring() -> bool`
- `await assess_current_state() -> CrisisAssessment`
- `await get_status_report() -> Dict[str, Any]`
- `await manual_intervention(intervention_type: str, context: Dict[str, Any] = None) -> bool`
- `await shutdown()`

### Factory

- `await create_rrt_advocate(...) -> RRTAdvocate`
  - Creates an instance and performs one initial assessment.

---

## 3) Runtime workflow

The runtime path in `RRTAdvocate` is:

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

## 4) Expected external integration points

`RRTAdvocate` imports the following modules from outside this repository snapshot:

- `crisis.detectors.crisis_detector.CrisisDetector`
- `crisis.assessors.crisis_assessor.CrisisAssessor`
- `response.interventions.intervention_manager.InterventionManager`
- `response.de_escalation.de_escalation_engine.DeEscalationEngine`
- `coordination.supervisor.supervisor_interface.SupervisorInterface`
- `learning.patterns.pattern_analyzer.PatternAnalyzer`

This means standalone execution in this repo alone will fail unless those modules are available on `PYTHONPATH`.

Minimal supervisor contract expected by `RRTAdvocate`:

```python
class SupervisorInterface:
    async def notify_advocate_status(self, advocate_id: str, status: str, user_id: str): ...
    async def handle_crisis(self, advocate_id: str, crisis_assessment, user_id: str): ...
    async def emergency_escalation(self, advocate_id: str, crisis_assessment, user_id: str): ...
```

---

## 5) Configuration runbook (`config/crisis_thresholds.yaml`)

The default config path is `config/crisis_thresholds.yaml`. It contains:

- crisis level ranges (`green`..`black`)
- indicator weights and thresholds
- crisis pattern definitions
- escalation rules
- intervention mappings by severity
- privacy/security/performance parameters

Important operational constraints:

- `RRTAdvocate._monitoring_loop()` currently sleeps for a fixed `1` second interval.
  - It does **not** currently consume per-level `monitoring_interval` values from YAML.
- Escalation behavior in code is driven by `assessment.user_safety_score` and `assessment.crisis_level`.
  - YAML escalation thresholds are consumed by external components (for example, detector/assessor) rather than directly in `RRTAdvocate`.

---

## 6) Developer setup (current repository state)

### Prerequisites

- Python 3.8+
- Access to the external NeuroLift modules listed in Section 4

### Suggested local workflow

1. Create and activate a virtual environment.
2. Ensure external dependency packages/modules are importable.
3. Run a basic import check:

```bash
python -c "from src.rrt_advocate import RRTAdvocate; print('import ok')"
```

4. Once dependencies are available, execute:

```bash
python src/rrt_advocate.py
```

---

## 7) Troubleshooting and common pitfalls

### `ModuleNotFoundError` for `crisis.*`, `response.*`, `coordination.*`, or `learning.*`

Cause: those modules are referenced but not vendored in this repository snapshot.

Fix: install/provide the dependent NeuroLift packages or run in the full multi-repo/monorepo environment where they exist.

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
