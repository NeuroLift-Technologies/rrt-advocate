# @neurolift-technologies/rrt-advocate

TypeScript port of the RRT Advocate **Crisis Detection Engine (CDE)** — a
3-layer, local-first crisis detection and assessment pipeline from the
[NeuroLift HAIEF Solidarity Framework](https://elevaitionfoundation.org).

> **Safety-critical.** This is a faithful port of the canonical Python CDE
> (`src/crisis/` in this repository). It preserves every layer weight,
> threshold, and confidence formula. The one intentional behavioral divergence
> (apostrophe fail-open in Layer 1) is documented in
> [`KNOWN_LIMITATIONS.md`](./KNOWN_LIMITATIONS.md). This package performs
> **detection and assessment only** — it does not generate responses,
> interventions, or persona-blended output.

## Install

```bash
npm install @neurolift-technologies/rrt-advocate
```

Runtime requirements:

- Node.js 20 or newer.
- ESM imports (`"type": "module"` package).
- No network service is required for detection or assessment.

`vader-sentiment` is an optional dependency. If installed, Layer 2 uses it for
polarity scoring; otherwise it falls back to a deterministic built-in heuristic.

## Usage

```ts
import { CrisisEngine, CrisisLevel } from "@neurolift-technologies/rrt-advocate";

const engine = new CrisisEngine("user-123");

const assessment = await engine.assess("I can't cope, everything is too much");

assessment.crisisLevel;          // CrisisLevel.GREEN | YELLOW | ORANGE | RED | BLACK
assessment.userSafetyScore;      // 1.0 (safe) → 0.05 (immediate danger)
assessment.confidenceScore;      // aggregate crisis confidence, 0.0–1.0
assessment.recommendedInterventions;
assessment.primaryIndicators;

if (assessment.crisisLevel !== CrisisLevel.GREEN) {
  // route to appropriate support
}
```

Use one `CrisisEngine` per user session. Layer 2 keeps a sentiment window and
Layer 3 keeps recent behavioral metadata, so reusing an engine across unrelated
sessions can mix trend signals. Call `resetSession()` when a conversation or
user session boundary is reached.

### The pipeline

| Layer | Module | Weight | Signal |
|---|---|---|---|
| 1 | `KeywordLayer` | 0.45 | Semantic-field keyword matching (self-harm forces 1.0) |
| 2 | `SentimentLayer` | 0.35 | Polarity & declining-trend detection over a sliding window |
| 3 | `BehavioralLayer` | 0.20 | Latency, message complexity, and looping (Jaccard) |

`CrisisDetector` aggregates the three layers into `CrisisIndicators`;
`CrisisAssessor` maps those to a `CrisisAssessment` using
`config/crisis_thresholds.yaml`. `CrisisEngine` wires the two together.

## Public API

### `CrisisEngine`

The facade most integrations should use.

```ts
const engine = new CrisisEngine("user-123", {
  // Optional: point at an approved crisis_thresholds.yaml copy.
  configPath: "./config/crisis_thresholds.yaml",

  // Optional: pass null to force the deterministic heuristic sentiment scorer.
  sentimentAnalyzer: null,
});

const indicators = await engine.detect("everything feels impossible");
const assessment = await engine.assess("everything feels impossible");

engine.resetSession();
```

- `detect(message?, timestamp?)` returns raw `CrisisIndicators` from the 3-layer
  detector.
- `assess(message?, timestamp?)` returns a `CrisisAssessment`.
- `resetSession()` clears the sentiment and behavioral windows.

The optional `timestamp` labels the returned indicators/assessment. Layer 3
response-latency tracking currently uses the runtime clock when `analyze()` runs.

### Lower-level exports

Use these for testing, diagnostics, or custom orchestration where you need layer
outputs before assessment:

```ts
import {
  CrisisDetector,
  CrisisAssessor,
  KeywordLayer,
  SentimentLayer,
  BehavioralLayer,
} from "@neurolift-technologies/rrt-advocate";
```

| Export | Purpose |
|---|---|
| `KeywordLayer` | Detects semantic distress fields and keyword matches. |
| `SentimentLayer` | Scores polarity and tracks a 5-message trend window by default. |
| `BehavioralLayer` | Tracks latency, complexity, and looping over recent messages. |
| `CrisisDetector` | Runs all three layers and aggregates weighted confidence. |
| `CrisisAssessor` | Maps aggregate confidence to a crisis level and interventions. |
| `CrisisLevel` | Enum values: `stable`, `elevated`, `high`, `critical`, `emergency`. |

## Assessment output

`CrisisAssessment` includes:

- `crisisLevel`: `GREEN`, `YELLOW`, `ORANGE`, `RED`, or `BLACK`.
- `confidenceScore`: weighted aggregate from the detector layers.
- `userSafetyScore`: inverse safety estimate from `1.0` down to `0.05`.
- `primaryIndicators` / `secondaryIndicators`: human-readable detected signals.
- `recommendedInterventions`: names loaded from the bundled thresholds YAML when
  available, or built-in defaults if the file cannot be read.
- `contextFactors.layer_scores`: keyword, sentiment, and behavioral confidence
  contributions for debugging and explainability.

Self-harm risk detected by Layer 1 forces aggregate confidence to `1.0`, maps the
assessment to `CrisisLevel.BLACK`, and sets `userSafetyScore` to `0.05`.

## Privacy

Everything runs locally. The behavioral layer stores only message metadata
(timing, length, and HMAC-hashed word tokens) — never raw message content.

Important persistence boundary: `CrisisIndicators` intentionally contains
`rawText`, keyword `matchedText`, and sentiment `textSnippet` for local debugging
and explainability. Do not persist raw detector outputs unless the user has opted
in and your integration has an approved redaction/storage path.

`RRT_BEHAVIORAL_TOKEN_KEY` may be set to control the HMAC key used for behavioral
word-token hashing. If it is not set, a random process-local key is generated.

## Configuration constraints

- The bundled `config/crisis_thresholds.yaml` is a vendored copy of the
  repository-level thresholds file.
- Threshold changes are safety-critical and require escalation under the repo
  governance contract.
- `configPath` is for pointing at an approved copy; it should not be used to
  experiment with unreviewed crisis thresholds.
- If the thresholds file cannot be loaded, the assessor logs a warning and uses
  built-in default intervention names. Confidence-to-level thresholds remain the
  code-defined Python-compatible ranges.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `SyntaxError` or `ERR_REQUIRE_ESM` from CommonJS | Package is ESM-only. | Use `import` syntax or dynamic `import()` from CommonJS. |
| Sentiment scores differ between environments | `vader-sentiment` is optional and may be present in one environment but absent in another. | Pass `sentimentAnalyzer: null` in deterministic tests. |
| Looping or decline signals do not appear on the first message | Sentiment and behavioral layers need session history. | Reuse one engine within a session; do not expect trend signals from a single isolated message. |
| Old conversation affects new assessments | Detector state was reused across a session boundary. | Call `resetSession()` or create a fresh `CrisisEngine`. |
| Warning about missing `crisis_thresholds.yaml` | `configPath` is wrong or the bundled file was not published/copied. | Verify package files include `config/` or pass a valid approved thresholds path. |

## Development

```bash
cd packages/rrt-advocate
npm install
npm run build   # tsc → dist/
npm test        # vitest
```

The test suite forces the deterministic sentiment fallback where exact scores
matter, and also exercises the auto-detected optional VADER path to catch loader
regressions.

## License

Apache-2.0 © NeuroLift Technologies, LLC
