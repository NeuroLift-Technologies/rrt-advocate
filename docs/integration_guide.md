# NeuroLift Ecosystem Integration Guide

This guide documents the **current, code-verified integration surface** for this repository.
It intentionally avoids speculative architecture and focuses on behavior implemented in:

- `src/rrt_advocate.py`
- `src/crisis/detectors/`
- `src/crisis/assessors/crisis_assessor.py`
- `config/crisis_thresholds.yaml`

> Safety-critical note: this repository is governed by ORG-DEV-OTOI-1.0.0. Do not modify crisis logic or thresholds without explicit approval.

---

## 1) What this repository currently provides

This repository now contains both the local-first Crisis Detection Engine (CDE) and
the async `RRTAdvocate` orchestration layer.

The CDE:

1. Runs keyword/semantic-field, sentiment, and behavioral analysis locally.
2. Aggregates layer scores into `CrisisIndicators`.
3. Hands those indicators to `CrisisAssessor` for crisis-level mapping.

`RRTAdvocate`:

1. Runs continuous crisis assessments in a monitoring loop.
2. Routes non-green assessments into tiered intervention flows.
3. Escalates emergencies to a supervisor interface (if provided).
4. Exposes status/reporting and manual intervention hooks for operators.

The primary entry point is `src/rrt_advocate.py`; the detector implementation lives
under `src/crisis/detectors/`.

---

## 2) Public interfaces (codepaths you can integrate with)

### Enums

- `CrisisLevel`: `GREEN`, `YELLOW`, `ORANGE`, `RED`, `BLACK`
- `ResponseStatus`: `PENDING`, `ACTIVE`, `SUCCESSFUL`, `ESCALATED`, `FAILED`
- `KeywordSemanticField`:
  - `NEGATIVE_SELF_TALK`
  - `TASK_AVOIDANCE`
  - `OVERWHELM`
  - `MELTDOWN`
  - `SHUTDOWN`
  - `HYPERFOCUS_LOOP`
  - `SELF_HARM_RISK`

### Data models

- `KeywordAnalysisResult`
  - Includes detected semantic fields, pattern matches, confidence score,
    self-harm flag, and primary field.
- `SentimentAnalysisResult`
  - Includes the current polarity reading, window average, polarity drop,
    trend, confidence score, and recent window values.
- `BehavioralAnalysisResult`
  - Includes response latency, complexity score/trend, looping detection,
    looping similarity, confidence score, and metadata metrics.
- `CrisisIndicators`
  - Aggregates all three detector-layer outputs plus self-harm risk,
    semantic fields, sentiment trend, behavioral signals, layer scores,
    and aggregate confidence.
- `CrisisAssessment`
  - Includes `crisis_level`, `confidence_score`, `user_safety_score`,
    `recommended_interventions`, and `context_factors`.
- `InterventionResponse`
  - Tracks intervention lifecycle (`start_time`, `end_time`, `status`, `effectiveness_score`).

### CDE classes

- `KeywordLayer().analyze(text: str) -> KeywordAnalysisResult`
- `SentimentLayer(window_size: int = 5).analyze(text: str) -> SentimentAnalysisResult`
- `SentimentLayer.reset_window()`
- `BehavioralLayer(window_size: int = 5).analyze(text: str) -> BehavioralAnalysisResult`
- `BehavioralLayer.reset()`
- `CrisisDetector(config_path: str = "config/crisis_thresholds.yaml")`
- `await CrisisDetector.detect_crisis_indicators(message: str = "", timestamp: Optional[datetime] = None) -> CrisisIndicators`
- `CrisisDetector.reset_session()`

### Main class

- `RRTAdvocate(user_id: str, config_path: str = "config/crisis_thresholds.yaml", toi_config: Optional[TOIConfig] = None, supervisor_interface: Optional[SupervisorInterface] = None)`
- `await process_message(user_message: str) -> Dict[str, Any]`
- `await select_stage_option(option_key: str, free_text: Optional[str] = None) -> Dict[str, Any]`
- `await start_monitoring() -> bool`
- `await stop_monitoring() -> bool`
- `await assess_current_state(message: str = "") -> CrisisAssessment`
- `await get_status_report() -> Dict[str, Any]`
- `await manual_intervention(intervention_type: str, context: Dict[str, Any] = None) -> bool`
- `await shutdown()`

### Factory

- `await create_rrt_advocate(...) -> RRTAdvocate`
  - Creates an instance. It does not perform an initial assessment.
- `create_toi_config(...) -> TOIConfig`
  - Builds a TOI config for tone, pacing, scaffolding level, silent-mode
    preference, timer preference, and persona preferences.

---

## 3) Runtime workflows

### Conversational path (`process_message`)

1. `process_message(user_message)` runs `CrisisDetector.detect_crisis_indicators(...)`.
2. `CrisisAssessor.assess_crisis(...)` maps indicators to a `CrisisAssessment`.
3. The dialogue tree receives the latest crisis score.
4. If OTOI consent has not been granted, the method returns the Stage 1 entry
   prompt with `requires_consent=True`.
5. If self-harm risk is detected, `_emergency_escalation(...)` runs and the
   response includes crisis resources.
6. Non-green assessments route through `_handle_crisis(...)` before the dialogue
   tree produces the user-facing response.
7. The returned dict includes dialogue data plus `crisis_level`,
   `crisis_confidence`, and `response_time_seconds`.

### Background monitoring path

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

## 4) Import paths and integration points

The main entry point imports repo-local packages as top-level modules:

- `crisis.detectors.crisis_detector.CrisisDetector`
- `crisis.assessors.crisis_assessor.CrisisAssessor`
- `response.interventions.intervention_manager.InterventionManager`
- `response.de_escalation.de_escalation_engine.DeEscalationEngine`
- `coordination.supervisor.supervisor_interface.SupervisorInterface`
- `learning.patterns.pattern_analyzer.PatternAnalyzer`

Those modules live under `src/`. Direct execution via `python src/rrt_advocate.py`
works because `src/rrt_advocate.py` adds its own directory to `sys.path`. For
one-off imports, tests, or host applications, ensure `src` is importable
(`PYTHONPATH=src` is the simplest local option).

Supervisor integration is optional. If no supervisor is provided, `RRTAdvocate`
uses `LocalSupervisor`, which logs locally and does not transmit data.

Minimal custom supervisor contract expected by `RRTAdvocate`:

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

- `CrisisDetector` accepts `config_path` for interface symmetry, but the detector
  itself is config-free. Its regex patterns, layer weights, sentiment thresholds,
  behavioral thresholds, and aggregate weights are defined in code.
- `CrisisAssessor` loads the YAML file and currently uses `intervention_mapping`
  for recommended interventions.
- `CrisisAssessor` maps aggregate confidence to levels using code-defined ranges:
  `GREEN <0.20`, `YELLOW <0.40`, `ORANGE <0.70`, `RED <0.90`, `BLACK >=0.90`.
- `RRTAdvocate._monitoring_loop()` currently sleeps for a fixed `1` second interval.
  - It does **not** currently consume per-level `monitoring_interval` values from YAML.
- Escalation behavior in code is driven by `assessment.user_safety_score` and `assessment.crisis_level`.
  - YAML escalation thresholds are not currently consumed directly by `RRTAdvocate`.

Do not treat YAML edits as a safe way to tune detector sensitivity without code
review; detector behavior is safety-critical source code.

---

## 6) Privacy and local-first CDE behavior

The CDE runs without external APIs.

- Layer 1 keyword analysis uses local, case-insensitive regex patterns.
- Layer 2 sentiment analysis uses `vaderSentiment` when installed. If it is not
  installed, the layer falls back to a local heuristic lexicon. The fallback
  notice is emitted lazily when the first `SentimentLayer` is instantiated, not
  at import time.
- Layer 3 behavioral analysis stores message metadata only:
  - timestamp
  - word count
  - character count
  - sentence count
  - punctuation density
  - non-reversible SHA-1 token hashes for word-overlap looping detection

Behavioral tracking does not store raw message content. `CrisisIndicators.raw_text`
does carry the current message through the in-memory assessment result, so
integrations must avoid persisting or exporting it unless the user has explicitly
consented.

---

## 7) Developer setup (current repository state)

### Prerequisites

- Python 3.10+
- `PyYAML` for `CrisisAssessor` config loading
- `pytest` and `pytest-asyncio` for the test suite
- Optional: `vaderSentiment` for more accurate local sentiment scoring

### Suggested local workflow

1. Create and activate a virtual environment.
2. Install local test/runtime dependencies:

```bash
python -m pip install -U pip pytest pytest-asyncio PyYAML
# Optional sentiment analyzer:
python -m pip install vaderSentiment
```

3. Run CDE tests:

```bash
pytest tests/test_cde.py
```

4. Run the broader currently passing local suites:

```bash
pytest tests/test_dialogue_tree.py tests/test_fusion_engine.py tests/test_toi.py
```

5. Run a basic import check:

```bash
python -c "from src.rrt_advocate import RRTAdvocate; print('import ok')"
```

6. Exercise the CDE directly:

```bash
PYTHONPATH=src python - <<'PY'
import asyncio
from crisis.detectors.crisis_detector import CrisisDetector

async def main():
    detector = CrisisDetector()
    indicators = await detector.detect_crisis_indicators(
        "I'm overwhelmed and stuck in a loop"
    )
    print(indicators.aggregate_confidence)
    print(indicators.get_primary_indicators())

asyncio.run(main())
PY
```

7. Run the interactive demo:

```bash
python src/rrt_advocate.py
```

If your shell has no `python` shim, use `python3` for the same commands. In the
current source snapshot, `python -m pytest` reaches 110 passing tests and then
fails in `tests/test_rrt_advocate.py` because that legacy stub harness does not
export `CrisisIndicators`, which `src/rrt_advocate.py` now imports. Use the
focused commands above until the harness is updated.

---

## 8) Troubleshooting and common pitfalls

### `ModuleNotFoundError` for `crisis.*`, `toi.*`, `response.*`, `coordination.*`, or `learning.*`

Cause: the repo-local `src/` directory is not on `PYTHONPATH`.

Fix: run through `python src/rrt_advocate.py`, import via `src.rrt_advocate`,
or set `PYTHONPATH=src` for top-level package imports.

### `ModuleNotFoundError: No module named 'yaml'`

Cause: `CrisisAssessor` imports `yaml` to load `config/crisis_thresholds.yaml`.

Fix: install `PyYAML` in the active environment.

### `python: command not found`

Cause: some Linux images provide `python3` without a `python` shim.

Fix: use `python3` and `python3 -m pip`, or activate a virtual environment that
provides `python`.

### Full `pytest` fails in `tests/test_rrt_advocate.py`

Cause: the current `tests/test_rrt_advocate.py` stub harness installs a fake
`crisis.detectors.crisis_detector` module that exports `CrisisDetector` but not
`CrisisIndicators`; `src/rrt_advocate.py` imports both.

Fix: for detector validation, run `pytest tests/test_cde.py`. For the currently
passing non-advocate suites, run `pytest tests/test_dialogue_tree.py
tests/test_fusion_engine.py tests/test_toi.py`. Update the legacy stubs before
using full-suite `pytest` as an all-green gate.

### Sentiment output differs between machines

Cause: `SentimentLayer` uses `vaderSentiment` when installed and a simpler local
heuristic fallback when it is not installed.

Fix: install `vaderSentiment` in environments where closer parity is required,
or test both codepaths when validating fallback behavior.

### Behavioral layer appears to store unreadable words

Cause: Layer 3 intentionally stores SHA-1 token hashes for word-overlap looping
detection. This preserves Jaccard similarity checks without retaining plaintext
message words.

Fix: do not replace these hashes with raw words in logs, telemetry, or persisted
records.

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

## 9) Operational runbook for service owners

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

## 10) Known documentation boundaries

This guide intentionally documents only behavior verifiable in this repository.
For roadmap plans, ecosystem proposals, or architectural intent not yet implemented here, treat those artifacts as design references rather than runtime truth.
