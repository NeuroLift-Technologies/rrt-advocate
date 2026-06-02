# Claude Audit — Governance Restoration (supersedes PR #16)

**Date:** 2026-05-28
**Agent:** Claude Code (`CLAUDE-CODE`)
**Branch:** `claude/governance-docs-restore-yB5sI`
**Supersedes:** PR #16 (`governance/otoi-compliance`, Copilot)
**Authority:** Joshua W. Dorsey, Sr.
**Governance:** ORG-DEV-OTOI-1.0.0

---

## Context

PR #16 ran a global find/replace from `.github-private` → `rrt-advocate`. Some
substitutions were correct (repo-local artifacts) but most destroyed org-level
governance framing that intentionally references the canonical
`NeuroLift-Technologies/.github-private` source. This restoration pass applies
only the correct subset and preserves all org-level framing on `main`.

This work is part of a coordinated 11-repo cleanup. Reference:
https://github.com/NeuroLift-Technologies/nlt-agent-1/pull/4

## Changes applied (the correct subset)

1. `README.md` — added `ai_assistant_directive` YAML block under the title.
2. `.nltotoi/.nltotoi/README.md` — `.github-private` → `rrt-advocate`.
3. `.nltotoi/.nltotoi/index/governance-files.md` — repo-local header + Scope.
4. `.nltotoi/.nltotoi/proposals/validation-roadmap.md` — repo-local Scope.
5. `.nltotoi/.nltotoi/scripts/validate-governance.sh` — `check_content` matches
   the local manifest's `NeuroLift-Technologies/rrt-advocate` value.
6. `nltotoi.json` — `repository.name` set to `NeuroLift-Technologies/rrt-advocate`;
   `last_updated` bumped to `2026-05-28`. `purpose`, `visibility: private`, and
   the canonical `public_governance` URL were preserved from `main`.
7. `SOPs/repo-governance-setup.md` — upgraded from v1.0.0 to canonical v1.1.0.
8. `docs/agent-log/2026-05-21-codex-repo-specific-governance.md` — preserved
   Copilot's audit log from PR #16.

## Files preserved from main (not touched)

`NLT-DEV-OTOI.md`, `AGENTS.md`, `CLAUDE.md`, `SOPs/incident-response.md`,
`SOPs/new-agent-onboarding.md`, `agents/nlt-governance-steward.md`,
`file-structure.md`, `docs/escalations/README.md`, and historical agent-log
records.

## Typo bug avoided

PR #16's blanket substitution turned `SOPs/incident-response.md` line 191 into
a literal `.github-repository` string — a non-existent path that would have
broken any agent following that SOP. This restoration **did not** apply that
edit; `SOPs/incident-response.md` is preserved from `main` and the
`.github-repository` typo is not present anywhere in this branch.

## Validation

`bash .nltotoi/.nltotoi/scripts/validate-governance.sh` was run after the edits.
See PR description for output.

---

*Audit log — NeuroLift Technologies | ORG-DEV-OTOI-1.0.0*
