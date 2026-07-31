# Deprecated / Archived Files

This directory contains files that were part of the legacy Python-era implementation of RRT Advocate. They have been superseded by the published packages and are preserved for historical reference only.

## What Was Archived

### Legacy Python RRT Advocate (superseded by PyPI `rrt-advocate@0.1.1`)
- `src/rrt_advocate.py` — legacy orchestrator entry point
- `src/crisis/` — legacy crisis detection (keyword, sentiment, behavioral layers, detector, assessor)
- `src/dialogue/` — legacy dialogue tree and stages
- `src/personas/` — legacy persona system (Ash, Sol, Echo, Kai, Myra, fusion engine)
- `src/coordination/` — legacy supervisor interface
- `src/learning/` — legacy pattern analyzer
- `src/response/` — legacy de-escalation and intervention
- `src/toi/` — legacy TOI/OTOI middleware
- `tests/` — legacy pytest suite

### Vendored Duplicates / Config
- `.nltotoi/.nltotoi/` — nested duplicate governance templates
- `templates/templates/` — nested duplicate templates
- `config/` — legacy Python configs (personas, TOI defaults, tone profiles)
- `data/` — legacy learning demo data
- `docs/integration_guide.md` — documents the deleted legacy orchestrator

### Tooling / Metadata
- `GEMINI_TOPOGRAPHY.py` — legacy repo topography
- `mcp-config.yaml` — legacy MCP server config
- `ISSUE_TEMPLATE/` — root issue templates (duplicated with `.github/ISSUE_TEMPLATE/`)
- `tests/` (root) — legacy test suite

## Current Canonical Packages

| Package | Source | Registry |
|---------|--------|----------|
| **npm** `@neurolift-technologies/rrt-advocate@0.1.1` | `packages/rrt-advocate/` | npm |
| **PyPI** `rrt-advocate@0.1.1` | `src/rrt_advocate/` | PyPI |
| **Cloudflare Worker** | Root `src/index.ts` + `wrangler.jsonc` | Cloudflare Workers |

## Migration Notes

- The npm package (`packages/rrt-advocate/`) is a TypeScript port of the Python Crisis Detection Engine
- The PyPI package (`src/rrt_advocate/`) is a Python port with identical functionality
- Both are generated from the same source of truth and maintained in parallel
- The Cloudflare Worker (root) is a separate deployment surface that embeds the logic
- Legacy Python code in `src/` (crisis/, dialogue/, etc.) was deleted in PR #42 and replaced by the `src/rrt_advocate/` port

