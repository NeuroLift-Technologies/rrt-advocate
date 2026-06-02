# Codex Audit — Repo-Specific Governance Scoping

**Date:** 2026-05-21
**Agent:** Codex (via GitHub Copilot)
**Branch:** `governance/otoi-compliance` (PR #16)
**Authority:** Joshua W. Dorsey, Sr.
**Governance:** ORG-DEV-OTOI-1.0.0

---

## Context

PR #16 (`governance/otoi-compliance`) was a Copilot baseline pass aimed at
re-scoping governance artifacts inside `rrt-advocate` so that repo-local
manifests, indexes, and validation scripts point at this repository rather than
at the canonical `NeuroLift-Technologies/.github-private` source.

The intent was correct: the local `.nltotoi/` namespace, `nltotoi.json` manifest,
and validation script should refer to `NeuroLift-Technologies/rrt-advocate` when
they describe **this repo's** governance footprint.

## Findings

Copilot's pass used a global find/replace from `.github-private` → `rrt-advocate`.
That approach was too broad and produced two distinct classes of changes:

1. **Correct (repo-local artifacts):**
   - `.nltotoi/README.md` namespace description
   - `.nltotoi/index/governance-files.md` header + Scope
   - `.nltotoi/proposals/validation-roadmap.md` Scope
   - `.nltotoi/scripts/validate-governance.sh` repo-name content check
   - `nltotoi.json` `repository.name`
   - `README.md` `ai_assistant_directive` YAML block

2. **Incorrect (over-trimmed org-level framing):**
   - `NLT-DEV-OTOI.md`, `AGENTS.md`, `CLAUDE.md`, `file-structure.md`,
     `SOPs/*.md`, `agents/nlt-governance-steward.md`,
     `docs/escalations/README.md`, historical agent-log records — these
     intentionally reference the canonical `.github-private` source and must
     not be repointed at this repo.
   - `nltotoi.json` — Copilot replaced `purpose` with a bland generic string,
     flipped `visibility` away from `private`, and rewrote `public_governance`
     away from the canonical `https://github.com/NeuroLift-Technologies/.github`
     URL. None of those changes are correct.

## Disposition

PR #16 should not be merged as-is. A follow-up pass will apply only the
correct subset and preserve all org-level framing.

---

*Audit log — NeuroLift Technologies | ORG-DEV-OTOI-1.0.0*
