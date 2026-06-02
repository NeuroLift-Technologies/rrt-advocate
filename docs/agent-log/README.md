# Agent Log — `rrt-advocate`

**Governance Standard**: ORG-DEV-OTOI-1.0.2

This directory contains the auditable agent activity log for this repository, as required by OTOI Sections 3, 5, and 7.

## Structure

```
docs/agent-log/
├── README.md              # This file
├── registrations/         # Agent self-registration records (.json)
├── intent/                # Intent log entries before significant actions (.md)
└── handoffs/              # Agent handoff records (.json)
```

Narrative governance audit notes may also live directly under `docs/agent-log/`
when they summarize a completed sync or restoration session.

## Session workflow

1. Read `NLT-DEV-OTOI.md`, `CLAUDE.md`, and `docs/active-threads.md`.
2. Register the session using `templates/agent-registration.json`.
3. Update `docs/active-threads.md` when opening, blocking, or completing a thread.
4. Write an intent log before broad-scope, irreversible, architectural, or sensitive actions.
5. Before ending a significant session, write a handoff record using `templates/handoff-record.json`.
6. Run `bash .nltotoi/scripts/validate-governance.sh` before opening a PR.

## File naming

- **Registrations**: `docs/agent-log/registrations/{date}-{agent-or-session}.json`
  - Example: `docs/agent-log/registrations/2026-06-01-claude-otoi-1.0.2-sync.json`
- **Intent logs**: `docs/agent-log/intent/{date}-{topic}.md`
  - Example: `docs/agent-log/intent/2026-06-02-docs-automation.md`
- **Handoffs**: `docs/agent-log/handoffs/{date}-{session-id}.json`
  - Example: `docs/agent-log/handoffs/2026-06-01-rrt-advocate-sync-handoff.json`

## Source templates and commands

- `templates/agent-registration.json` — OTOI Section 3 registration fields.
- `templates/intent-log.md` — OTOI Section 7 intent logging format.
- `templates/handoff-record.json` — OTOI Section 5 handoff fields.
- `.claude/commands/register-session.md`, `.claude/commands/intent-log.md`, and
  `.claude/commands/handoff.md` document Claude Code command wrappers for these records.

All records are committed to this repo for auditability. Keep entries factual:
only mark validation or tests as passing after the command has actually run.
