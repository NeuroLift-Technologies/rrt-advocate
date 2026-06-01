# Governance Inventory & Status — OTOI 1.0.2 Sync

**Date:** 2026-06-01
**Agent:** Claude Code (`CLAUDE-CODE`)
**Branch:** `claude/rrt-advocate-sync-handoff-8uII8` (built on PR #17, `claude/governance-docs-restore-yB5sI`)
**Authority:** Joshua W. Dorsey, Sr.
**Governance:** ORG-DEV-OTOI-1.0.2
**Canonical source:** `NeuroLift-Technologies/.github-private`

---

## Purpose

Bring the `rrt-advocate` governance overlay up to date with canonical NLT governance, deliver an
inventory/status of the repo handoff, and write a session handoff record.

The repo was pinned to the superseded **ORG-DEV-OTOI-1.0.0**. Mid-session, Joshua provided the
new authoritative contract **ORG-DEV-OTOI-1.0.2** (dated 2026-06-01), which is one step ahead of
the `.github-private` clone in this environment (still 1.0.1). Per Joshua's instruction the sync
targets **1.0.2** directly.

> **Source-of-truth note:** `.github-private` here still holds 1.0.1. This sync therefore lands
> 1.0.2 in `rrt-advocate` *ahead of* the canonical repo. A follow-up must land the same 1.0.2
> contract into `.github-private` so the source-of-truth leads org-wide propagation. Flagged in
> the handoff as a pending action.

## The three-tier governance model

| Tier | Repo | Role |
|---|---|---|
| 1 — Public identity | `.github` | Solidarity Framework / HAIEF; governance pushed *up* via `sync-governance-public.yml` |
| 2 — Private operational governance | **`.github-private`** | Canonical source: OTOI contract, templates, SOPs, `.claude/`, CI |
| 3 — Org product repo (**this repo**) | `rrt-advocate` | Repo-specific `CLAUDE.md` + synced governance set + synced `.claude/` |

The canonical sync spec is defined in `.github-private` by: `nltotoi.json` → `required_files[]`,
`SOPs/repo-governance-setup.md` (SOP-NLT-002), and `governance-auto-propagate.yml`.
**Correctly absent** from a product repo (not drift): `profile/`, `public-sync/`,
`agents-templates/`, and the live org `.github/workflows/` set.

## What ORG-DEV-OTOI-1.0.2 changed (vs 1.0.1)

- Corrected the acronym expansion: **TOI = "Terms of Interaction"**, **OTOI = "Orchestrated Terms
  of Interaction"** (the prior "Developer Operations & Team Orientation Index" was wrong). Fixed in
  the contract title and `.nltotoi/contracts/README.md`.
- Added **Section 11 — Change Log** to `NLT-DEV-OTOI.md`.

## Inventory of drift found, and disposition

| Item | State before | Action taken |
|---|---|---|
| OTOI version (all governance files) | pinned `1.0.0` | bumped to `1.0.2` |
| `NLT-DEV-OTOI.md` | stale 1.0.0 | replaced verbatim with Joshua's authoritative 1.0.2 upload |
| `.claude/` session template | **missing entirely** | added full canonical tree (README, settings.json, SessionStart hook, 3 agents, 5 commands, 7 skills); bumped to 1.0.2; hook executable |
| `.nltotoi/` layout | **corrupt nested `.nltotoi/.nltotoi/`** held real files; top-level partial — broke validator `REPO_ROOT` | flattened to single-level `.nltotoi/` |
| `templates/` layout | **corrupt nested `templates/templates/`** duplicate | removed; top-level holds canonical set |
| `nltotoi.json` `repository.name` | bug: `…/.github-private` | set to `…/rrt-advocate` |
| `nltotoi.json` version / required_files / discovery | 1.0.0; missing `.claude/`, `proposals`, `commit-message` | rewritten to 1.0.2 set (kept org-style identity: `visibility: private`, internal-governance purpose) |
| `AGENTS.md`, templates, ISSUE/PR templates, SOPs, `.nltotoi/contracts/README.md` | stale | synced canonical + bumped to 1.0.2 |
| `.nltotoi/scripts/validate-governance.sh` | stale + wrong location | synced canonical; bumped content-checks to 1.0.2; preserved repo-local repo-name check (`rrt-advocate`) |
| `CLAUDE.md` | repo-specific crisis stub, 1.0.0 refs | **kept stub**; bumped refs to 1.0.2; added `.claude/` note; refreshed `.nltotoi/` structure block |
| `.github/ISSUE_TEMPLATE/*`, `file-structure.md`, `docs/integration_guide.md` | 1.0.0 refs | version-bumped to 1.0.2 |
| `links.md`, `mcp-config.yaml` | already in sync | left unchanged |
| crisis code (`src/`, `config/crisis_thresholds.yaml`, `tests/`, `data/`, `GEMINI_TOPOGRAPHY.py`) | n/a | **untouched** (out of scope, safety-critical) |

## Repo-local vs canonical (the nuance that matters)

Two files are intentionally **repo-specific** — edited in place, not overwritten:
- **`CLAUDE.md`** — the safety-critical crisis-intervention session directive.
- **`nltotoi.json`** — keeps the `rrt-advocate` `repository` block (org-style: `visibility: private`,
  internal-governance purpose, per Joshua's choice).

The validator's manifest repo-name content check is the single legitimately repo-local line in
`validate-governance.sh` (canonical checks for `.github-private`; here it checks `rrt-advocate`).

## Notes / decisions

- Built on **PR #17** (`claude/governance-docs-restore-yB5sI`); this branch supersedes #17's partial scope.
- The botched Copilot **PR #16** (`governance/otoi-compliance`) should be **closed** — superseded.
- Manifest lists `.github/workflows/validate-governance.yml` (the enforced path that exists here),
  not the root `workflows/` doc copy that only exists in `.github-private`.

## Validation

```
bash .nltotoi/scripts/validate-governance.sh           -> 34 passed, 0 failed, 0 warned (exit 0)
```
`Repo:` now resolves to the repo root (confirms the flatten fixed the nested-layout defect).
Verbatim-synced files are byte-identical to their `.github-private` source (pre-1.0.2 bump);
`NLT-DEV-OTOI.md` is byte-identical to Joshua's 1.0.2 upload.

---

*Audit log — NeuroLift Technologies | ORG-DEV-OTOI-1.0.2*
