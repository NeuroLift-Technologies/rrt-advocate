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

- **Registrations**: When you begin a session, copy `templates/agent-registration.json`, fill it in, and save it as `docs/agent-log/registrations/{AGENT_NAME}-{SESSION_ID}.json`
- **Handoffs**: When ending an incomplete session, copy `templates/handoff-record.json`, fill it in, and save it as `docs/agent-log/handoffs/{AGENT_NAME}-{DATE}-handoff.json`

All records are committed to this repo for auditability.
