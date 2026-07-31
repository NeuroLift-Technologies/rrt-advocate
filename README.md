# RRT AIdvocAIte

**Real-Time Crisis Intervention & Protective Layer — Solidarity Framework**

> *"When burnout hits, the cavalry arrives."*

---

## 📦 Published Packages

| Runtime | Package | Version | Source | Registry |
|---------|---------|---------|--------|----------|
| **TypeScript (npm)** | `@neurolift-technologies/rrt-advocate` | `0.1.1` | `packages/rrt-advocate/` | [npm](https://www.npmjs.com/package/@neurolift-technologies/rrt-advocate) |
| **Python (PyPI)** | `rrt-advocate` | `0.1.1` | `src/rrt_advocate/` | [PyPI](https://pypi.org/project/rrt-advocate/) |
| **Cloudflare Worker** | `rrt-advocate` (worker) | — | Root `src/index.ts` | [Cloudflare Workers](https://developers.cloudflare.com/workers/) |

---

## ⚠️ PROTOTYPE — NOT A SAFETY SYSTEM

This is an **experimental** crisis-detection library with **stubbed/placeholder intervention layers**. It is **NOT medical advice, NOT a crisis service**, and performs **no real-time monitoring**. It **can miss real crisis signals** (known detection/recall gaps) — **do not rely on it as a safety net or as the sole safety mechanism**.

**If you or someone else needs help now:** in the US, call or text **988** (Suicide & Crisis Lifeline) or chat [988lifeline.org](https://988lifeline.org); in an emergency call **911**. Outside the US: [findahelpline.com](https://findahelpline.com).

---

## 🚀 Quick Start

### TypeScript (npm)

```bash
npm install @neurolift-technologies/rrt-advocate
```

```ts
import { CrisisDetector, CrisisAssessor, CrisisLevel } from '@neurolift-technologies/rrt-advocate';

const detector = new CrisisDetector({ loadVader: true });
const result = await detector.assess('I cannot go on anymore, everything is hopeless');
console.log(result.level); // CrisisLevel.Critical
```

### Python (PyPI)

```bash
pip install rrt-advocate
```

```python
from rrt_advocate import CrisisDetector, CrisisAssessor

detector = CrisisDetector()
result = detector.assess("I cannot go on anymore, everything is hopeless")
print(result.level)  # CrisisLevel.Critical
```

### Cloudflare Worker

Deploy the root worker which exposes `/api/chat` (streaming) and `/api/health` endpoints:

```bash
npm install -g wrangler
wrangler deploy
```

---

## 🏗️ Architecture

### Three Independent Surfaces

| Surface | Purpose | Language | Key Files |
|---------|---------|----------|-----------|
| **npm Package** | Library for Node.js/Edge apps | TypeScript | `packages/rrt-advocate/src/` |
| **PyPI Package** | Library for Python apps | Python | `src/rrt_advocate/` |
| **Cloudflare Worker** | HTTP API with streaming chat | TypeScript (Worker) | `src/index.ts`, `wrangler.jsonc` |

The npm and PyPI packages are **parallel ports** of the same Crisis Detection Engine (CDE) — they share identical logic (keyword layer, sentiment layer, behavioral layer, crisis assessor) but zero code/runtime coupling.

### Crisis Detection Engine (CDE)

```
User Input
    ↓
┌─────────────────────────────────────┐
│ 1. Keyword Layer (rule-based)       │
│    • self-harm lexicon              │
│    • hopelessness markers           │
│    • urgency indicators             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Sentiment Layer (VADER optional) │
│    • polarity scoring               │
│    • intensity weighting            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Behavioral Layer (stateful)      │
│    • escalation tracking            │
│    • protective low-demand mode     │
│    • session continuity             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Crisis Assessor                  │
│    • risk level: Stable/Elevated/   │
│      High/Critical                  │
│    • intervention recommendations   │
└─────────────────────────────────────┘
```

### Risk Levels

| Level | Description | Action |
|-------|-------------|--------|
| `Stable` | No crisis indicators | Monitor |
| `Elevated` | Some distress markers | Check-in recommended |
| `High` | Strong crisis signals | Immediate intervention |
| `Critical` | Imminent danger | Emergency resources |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `packages/rrt-advocate/README.md` | npm package usage |
| `packages/rrt-advocate/KNOWN_LIMITATIONS.md` | Known gaps (apostrophe fail-open, VADER optional) |
| `src/rrt_advocate/README.md` | PyPI package usage (mirror) |
| `docs/active-threads.md` | Current work threads |
| `docs/agent-log/` | Governance records |

---

## 🧪 Testing

```bash
# npm package tests
cd packages/rrt-advocate && npm test

# PyPI package tests
pip install pytest && python -m pytest src/rrt_advocate/

# Worker tests (manual)
wrangler dev
```

---

## 📜 License

Apache-2.0 — see `LICENSE` and `packages/rrt-advocate/LICENSE`.

---

## 🔗 Related

- **TOI** — Terms of Interaction: `@neurolift-technologies/toi`
- **OTOI** — Orchestrated TOI: `@neurolift-technologies/otoi`
- **Sleepwalker** — Emotional Continuity: `@neurolift-technologies/sleepwalker-protocol`
- **ASFDK** — Umbrella: `@neurolift-technologies/asfdk`
