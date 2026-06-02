# Governance File Index — NeuroLift Technologies `rrt-advocate`

**Last updated:** 2026-06-02  
**Maintained by:** `.nltotoi/` namespace tooling  
**Scope:** `NeuroLift-Technologies/rrt-advocate`

---

## Core Governance Files

| File | Type | Purpose | Required |
|---|---|---|---|
| `NLT-DEV-OTOI.md` | Contract | Org-level coding agent contract (ORG-DEV-OTOI-1.0.2) | ✅ |
| `AGENTS.md` | Gateway | Internal agent coordination gateway | ✅ |
| `nltotoi.json` | Manifest | Machine-readable discovery manifest | ✅ |
| `README.md` | Overview | Repository overview and purpose | ✅ |
| `file-structure.md` | ADR | Architecture decision record for this repo structure | ✅ |
| `CLAUDE.md` | Instructions | Agent session instructions and plan | ✅ |

---

## .nltotoi Namespace

| File | Purpose | Required |
|---|---|---|
| `.nltotoi/README.md` | Namespace overview | ✅ |
| `.nltotoi/index/governance-files.md` | This file — governance registry | ✅ |
| `.nltotoi/contracts/README.md` | Contract namespace and versioning | ✅ |
| `.nltotoi/scripts/validate-governance.sh` | Automated compliance validation | ✅ |
| `.nltotoi/proposals/validation-roadmap.md` | Planned validation improvements | ✅ |

---

## Templates

| File | Purpose | Source |
|---|---|---|
| `templates/agent-registration.json` | Agent self-registration format | OTOI Section 3 |
| `templates/handoff-record.json` | Session handoff format | OTOI Section 5 |
| `templates/escalation.md` | Escalation record format | OTOI Section 4.3 |
| `templates/intent-log.md` | Intent logging before action | OTOI Section 7 |
| `templates/commit-message.md` | Commit message format reference | OTOI Section 4.2, SOP-NLT-001 Step 7 |

---

## GitHub Templates

| File | Purpose |
|---|---|
| `ISSUE_TEMPLATE/agent-escalation.md` | GitHub issue form for agent escalations |
| `ISSUE_TEMPLATE/governance-proposal.md` | GitHub issue form for OTOI amendment proposals |
| `PULL_REQUEST_TEMPLATE/agent-contribution.md` | Agent PR checklist with governance requirements |

---

## CI Workflows

| File | Purpose | Trigger | SOP |
|---|---|---|---|
| `.github/workflows/validate-governance.yml` | Governance validation (runs validate-governance.sh) | push, pull_request | SOP-NLT-002 |

Only the workflow above is present in this product repo. Broader org automation
such as propagation, incident detection, and reusable checks belongs in the
canonical governance repo unless explicitly synced here.

---

## Composite Actions

| Path | Purpose |
|---|---|
| _None in this repo_ | Composite actions are not part of the current `rrt-advocate` governance overlay. |

---

## Agent Profiles — Repo-local (`agents/`)

| File | Purpose | Required |
|---|---|---|
| `agents/nlt-governance-steward.md` | Governance steward agent — enforces ORG-DEV-OTOI-1.0.2 | ✅ |

This repo does not currently contain `agents/README.md`, `agents/registry.json`,
or additional repo-local agent profiles.

---

## Agent Profiles — VS Code / GitHub Copilot Chat (`.github/agents/`)

| File | Purpose | Required |
|---|---|---|
| _None in this repo_ | `.github/agents/` is not part of the current `rrt-advocate` file set. | — |

---

## Claude Code Session Config (`.claude/`)

| Path | Purpose | Required |
|---|---|---|
| `.claude/README.md` | Claude Code template overview and repo-local override guidance | ✅ |
| `.claude/settings.json` | Wires the `SessionStart` hook | ✅ |
| `.claude/hooks/session-start.sh` | Prints the mandatory session-start reading order | ✅ |
| `.claude/hooks/README.md` | Hook behavior notes | ✅ |
| `.claude/agents/nlt-governance-steward.md` | Governance steward subagent profile | ✅ |
| `.claude/agents/nlt-code-reviewer.md` | Code review subagent profile | ✅ |
| `.claude/agents/swe-agent.md` | SWE implementation subagent profile | ✅ |
| `.claude/commands/*.md` | Slash-command runbooks for registration, handoff, escalation, intent logs, and governance checks | ✅ |
| `.claude/skills/*/SKILL.md` | NLT skill SOPs for OTOI, registration, handoff, escalation, intent logs, commit format, and incident response | ✅ |

Do not edit `.claude/` here for org-wide behavior. It is a synced template; use
`.claude/settings.local.json` for repo-local Claude Code overrides.

---

## SOPs (Standard Operating Procedures)

| File | Purpose |
|---|---|
| `SOPs/new-agent-onboarding.md` | How to onboard a new coding agent |
| `SOPs/repo-governance-setup.md` | How to add governance stubs to a new NLT repo |
| `SOPs/incident-response.md` | What to do when an agent goes off-rails |

---

## File Count Summary

| Category | Count |
|---|---|
| Core governance | 6 |
| .nltotoi namespace | 5 |
| Templates | 5 |
| GitHub templates | 3 |
| CI workflows | 1 |
| SOPs | 3 |
| Agent profiles (`agents/`) | 1 |
| Agent profiles (`.github/agents/`) | 0 |
| Claude Code session config (`.claude/`) | 19 |
| **Total indexed here** | **43** |

---

*Generated from `.nltotoi/index/governance-files.md` | NeuroLift Technologies | ORG-DEV-OTOI-1.0.2*
