# Known Limitations

This package is a faithful TypeScript port of the Python Crisis Detection
Engine (`src/crisis/` in this repository). Every layer weight, threshold,
confidence formula, and crisis-level mapping is a deliberate 1:1 of the
canonical Python — **with one documented exception**, recorded here so it is on
the record as an intentional divergence rather than accidental drift.

## 1. Apostrophe fail-open in Layer 1 (intentional divergence)

**Where:** `src/keywordLayer.ts` (Layer 1, keyword/semantic-field matching —
the 0.45-weighted layer).

**Python behavior:** Several Layer 1 patterns require a literal apostrophe,
e.g. `i (can't|cannot)`, `i('m| am)`, `i don't deserve`, `everything('s| is)`,
`i('ve| have)`. Voice-dictated and smart-quote input frequently arrives without
apostrophes (`cant`, `dont`, `wont`, `im`, `youre`, `everythings`). Under the
Python matcher those inputs silently **miss** the apostrophe-required patterns.

**Why this is the worst case:** Layer 1 carries the highest aggregation weight
(0.45). A miss here is the single most damaging false negative the engine can
produce, and dictation is a primary input mode for the neurodivergent users
this system exists to protect.

**Divergence:** Unlike the rest of the port, the Layer 1 matcher is made
apostrophe-**insensitive**. Apostrophes (`'`, `’`, `ʼ`) are stripped from both
the input text and the compiled patterns before matching, so `can't` and `cant`
match identically. This is fail-open: it only ever causes the same or *more*
distress signals to be detected — it never suppresses a match the Python would
have found. Weights, thresholds, confidence math, and self-harm escalation are
unchanged. This mirrors the apostrophe fail-open already adopted in `nlt-sdl`.

**Side effect:** Because matching runs against the apostrophe-stripped text,
`KeywordMatch.position` and `KeywordMatch.matchedText` index into the normalized
haystack, not the original string. These are debug/reporting fields only and do
not affect detection, confidence, or assessment.

## 2. Sentiment Layer (Layer 2) — optional VADER

Layer 2 uses `vader-sentiment` when it is installed (an `optionalDependency`,
matching the Python `vaderSentiment` optional import) and otherwise falls back
to the same lightweight heuristic lexicon as the Python source. Scores from the
JS and Python VADER implementations are expected to agree closely but are not
guaranteed bit-identical. The built-in heuristic fallback is fully deterministic
and is what the test suite exercises.

## 3. Scope — detection & assessment only

This package ports the **Crisis Detection Engine** (the 3-layer detectors, the
`CrisisDetector` aggregation, and the `CrisisAssessor`). The persona-fusion,
dialogue-tree, de-escalation, intervention, and TOI/OTOI *response* layers
remain Python-canonical and are intentionally **not** ported here.

## 4. Vendored thresholds must stay in sync

`config/crisis_thresholds.yaml` is a vendored copy of the canonical, safety-
critical thresholds file at the repository root. It must be kept in sync with
the canonical file; changes to crisis thresholds require escalation per the
repository governance contract.
