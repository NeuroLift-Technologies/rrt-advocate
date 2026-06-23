> ## ⚠️ PROTOTYPE — NOT A SAFETY SYSTEM
>
> This is an **experimental** crisis-detection library with **stubbed/placeholder intervention layers**. It is **NOT medical advice, NOT a crisis service**, and performs **no real-time monitoring**. It **can miss real crisis signals** (known detection/recall gaps) — **do not rely on it as a safety net or as the sole safety mechanism**.
>
> **If you or someone else needs help now:** in the US, call or text **988** (Suicide & Crisis Lifeline) or chat [988lifeline.org](https://988lifeline.org); in an emergency call **911**. Outside the US: [findahelpline.com](https://findahelpline.com).
>
> Provided **AS-IS, without warranty**.

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

### The pipeline

| Layer | Module | Weight | Signal |
|---|---|---|---|
| 1 | `KeywordLayer` | 0.45 | Semantic-field keyword matching (self-harm forces 1.0) |
| 2 | `SentimentLayer` | 0.35 | Polarity & declining-trend detection over a sliding window |
| 3 | `BehavioralLayer` | 0.20 | Latency, message complexity, and looping (Jaccard) |

`CrisisDetector` aggregates the three layers into `CrisisIndicators`;
`CrisisAssessor` maps those to a `CrisisAssessment` using
`config/crisis_thresholds.yaml`. `CrisisEngine` wires the two together.

Lower-level building blocks are exported too:

```ts
import {
  CrisisDetector,
  CrisisAssessor,
  KeywordLayer,
  SentimentLayer,
  BehavioralLayer,
} from "@neurolift-technologies/rrt-advocate";
```

## Privacy

Everything runs locally. The behavioral layer stores only message metadata
(timing, length, and HMAC-hashed word tokens) — never raw message content.

## Development

```bash
npm install
npm run build   # tsc → dist/
npm test        # vitest
```

## License

Apache-2.0 © NeuroLift Technologies, LLC
