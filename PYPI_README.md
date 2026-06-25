> ## ⚠️ PROTOTYPE — NOT A SAFETY SYSTEM
>
> This is an **experimental** crisis-detection library with **stubbed/placeholder intervention layers**. It is **NOT medical advice, NOT a crisis service**, and performs **no real-time monitoring**. It **can miss real crisis signals** (known detection/recall gaps) — **do not rely on it as a safety net or as the sole safety mechanism**.
>
> **If you or someone else needs help now:** in the US, call or text **988** (Suicide & Crisis Lifeline) or chat [988lifeline.org](https://988lifeline.org); in an emergency call **911**. Outside the US: [findahelpline.com](https://findahelpline.com).
>
> Provided **AS-IS, without warranty**.

# rrt-advocate (Python)

Python port of the RRT Advocate **Crisis Detection Engine (CDE)** — a 3-layer,
local-first crisis detection and assessment pipeline from the
[NeuroLift HAIEF Solidarity Framework](https://elevaitionfoundation.org).

This is a faithful port of the published npm package
[`@neurolift-technologies/rrt-advocate`](https://github.com/NeuroLift-Technologies/rrt-advocate)
(the TypeScript CDE, which is the **source of truth** for this port). The public
API mirrors the npm package's surface in snake_case.

> **Safety-critical.** This port preserves every layer weight, threshold, and
> confidence formula from the TypeScript source. The one intentional behavioral
> divergence (apostrophe fail-open in Layer 1) is documented in
> [`KNOWN_LIMITATIONS.md`](./KNOWN_LIMITATIONS.md). This package performs
> **detection and assessment only** — it does not generate responses,
> interventions, or persona-blended output.

## Install

```bash
pip install rrt-advocate
```

`vaderSentiment` is an optional dependency. If installed, Layer 2 uses it for
polarity scoring; otherwise it falls back to a deterministic built-in heuristic.

## Usage

```python
from rrt_advocate import CrisisEngine, CrisisLevel

engine = CrisisEngine("user-123")

assessment = engine.assess("I can't cope, everything is too much")

assessment.crisis_level             # CrisisLevel.GREEN | YELLOW | ORANGE | RED | BLACK
assessment.user_safety_score        # 1.0 (safe) → 0.05 (immediate danger)
assessment.confidence_score         # aggregate crisis confidence, 0.0–1.0
assessment.recommended_interventions
assessment.primary_indicators

if assessment.crisis_level is not CrisisLevel.GREEN:
    ...  # route to appropriate support
```

### The pipeline

| Layer | Module | Weight | Signal |
|---|---|---|---|
| 1 | `KeywordLayer` | 0.45 | Semantic-field keyword matching (self-harm forces 1.0) |
| 2 | `SentimentLayer` | 0.35 | Polarity & declining-trend detection over a sliding window |
| 3 | `BehavioralLayer` | 0.20 | Latency, message complexity, and looping (Jaccard) |

`CrisisDetector` aggregates the three layers into `CrisisIndicators`;
`CrisisAssessor` maps those to a `CrisisAssessment` using the bundled
`config/crisis_thresholds.yaml`. `CrisisEngine` wires the two together.

Lower-level building blocks are exported too:

```python
from rrt_advocate import (
    CrisisDetector,
    CrisisAssessor,
    KeywordLayer,
    SentimentLayer,
    BehavioralLayer,
)
```

## Privacy

Everything runs locally. The behavioral layer stores only message metadata
(timing, length, and HMAC-hashed word tokens) — never raw message content.

## License

Apache-2.0 © NeuroLift Technologies, LLC
