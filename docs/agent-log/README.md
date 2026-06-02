# Agent Log — `rrt-advocate`

**Governance Standard**: ORG-DEV-OTOI-1.0.0

This directory contains the auditable agent activity log for this repository, as required by OTOI Section 5.

## Structure

```
docs/agent-log/
├── README.md              # This file
├── registrations/         # Agent self-registration records (.json)
└── handoffs/              # Agent handoff records (.json)
```

## Usage

- **Registrations**: At session start, copy `templates/agent-registration.json`, fill it in, and save it under `docs/agent-log/registrations/`.
- **Handoffs**: At session end, copy `templates/handoff-record.json`, fill it in, and save it under `docs/agent-log/handoffs/` when the work is significant, incomplete, or likely to be resumed by another agent.

All records are committed to this repo for auditability.

## Registration checklist

Before editing files, each agent should:

1. Read `NLT-DEV-OTOI.md`, `AGENTS.md`, `CLAUDE.md`, and `docs/active-threads.md`.
2. Check for active-thread conflicts.
3. Write a registration record that truthfully reflects the current session.

Recommended filename:

```text
docs/agent-log/registrations/{AGENT_NAME}-{SESSION_ID}.json
```

If an automation reuses a session ID across multiple runs, append a short date
or task slug so the new record does not overwrite a previous audit entry:

```text
docs/agent-log/registrations/CURSOR-158b2152-7214-45b1-9efe-a458133e75b6-2026-06-02-docs.json
```

Record constraints:

- Set `scope_confirmed_by_human` to `false` for unattended automation triggers
  unless the prompt explicitly includes human confirmation.
- Mark each `steps_completed` value based on what actually happened in the
  session.
- Use `escalation_needed=true` when a required governance source is unavailable
  or the task touches crisis logic, safety thresholds, architecture, production
  deployment, external integrations, or other OTOI escalation triggers.

## Handoff checklist

Use handoffs to make the next session easy to resume. A useful handoff includes:

- what changed and why;
- files modified;
- validation commands run and whether they passed;
- open blockers or escalations;
- any work intentionally left undone.

Recommended filename:

```text
docs/agent-log/handoffs/{YYYY-MM-DD}-{AGENT_OR_SESSION_SLUG}.json
```

For documentation-only sessions, list documentation validation commands such as:

```bash
bash .nltotoi/scripts/validate-governance.sh
python -m json.tool docs/agent-log/registrations/<record>.json >/dev/null
git diff --check
```

Do not claim runtime tests passed unless the runtime code was actually executed.

## Active-thread coordination

`docs/active-threads.md` is the live coordination surface. Update it when:

- starting a thread that could conflict with another agent;
- resolving or handing off a thread;
- documenting that work is blocked pending Joshua W. Dorsey, Sr.'s review.

Keep agent-log records and active-thread status consistent before committing.
