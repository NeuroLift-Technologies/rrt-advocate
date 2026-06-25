# Known Limitations

This package is a faithful Python port of the published npm Crisis Detection
Engine, `@neurolift-technologies/rrt-advocate` (the TypeScript CDE, which is the
source of truth). Every layer weight, threshold, confidence formula, and
crisis-level mapping is a deliberate 1:1 of the TypeScript source — **with one
documented exception**, recorded here so it is on the record as an intentional
divergence rather than accidental drift.

## 1. Apostrophe fail-open in Layer 1 (intentional divergence)

**Where:** `rrt_advocate/keyword_layer.py` (Layer 1, keyword/semantic-field
matching — the 0.45-weighted layer).

**Canonical behavior:** Several Layer 1 patterns require a literal apostrophe,
e.g. `i (can't|cannot)`, `i('m| am)`, `i don't deserve`, `everything('s| is)`,
`i('ve| have)`. Voice-dictated and smart-quote input frequently arrives without
apostrophes (`cant`, `dont`, `wont`, `im`, `youre`, `everythings`). Under a
strict matcher those inputs silently **miss** the apostrophe-required patterns.

**Why this is the worst case:** Layer 1 carries the highest aggregation weight
(0.45). A miss here is the single most damaging false negative the engine can
produce, and dictation is a primary input mode for the neurodivergent users
this system exists to protect.

**Divergence:** Unlike the rest of the port, the Layer 1 matcher is made
apostrophe-**insensitive**. Apostrophes (`'`, `’`, `ʼ`) are stripped from both
the input text and the compiled patterns before matching, so `can't` and `cant`
match identically. This is fail-open: it only ever causes the same or *more*
distress signals to be detected — it never suppresses a match a strict matcher
would have found. Weights, thresholds, confidence math, and self-harm escalation
are unchanged. This matches the npm source and mirrors the apostrophe fail-open
adopted in `nlt-sdl`.

**Side effect:** Because matching runs against the apostrophe-stripped text,
`KeywordMatch.matched_text` and `KeywordMatch.position` index into the normalized
haystack, not the original string. These are debug/reporting fields only and do
not affect detection, confidence, or assessment.

## 2. Sentiment Layer (Layer 2) — optional VADER

Layer 2 uses `vaderSentiment` when it is installed (an optional dependency,
matching the npm `vader-sentiment` `optionalDependency`) and otherwise falls
back to the same lightweight heuristic lexicon as the source. Scores from the
JS and Python VADER implementations are expected to agree closely but are not
guaranteed bit-identical. The built-in heuristic fallback is fully deterministic
and is what the test suite exercises.

## 3. Scope — detection & assessment only

This package ports the **Crisis Detection Engine** (the 3-layer detectors, the
`CrisisDetector` aggregation, and the `CrisisAssessor`). The persona-fusion,
dialogue-tree, de-escalation, intervention, and TOI/OTOI *response* layers
remain canonical elsewhere and are intentionally **not** ported here.

## 4. Vendored thresholds must stay in sync

`config/crisis_thresholds.yaml` (bundled inside `rrt_advocate/config/`) is a
vendored copy of the canonical, safety-critical thresholds file. It must be kept
in sync with the canonical file; changes to crisis thresholds require escalation
per the repository governance contract.
