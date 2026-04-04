# AGENTS.md — Agent Coordination Protocol for `rrt-advocate`

**Governance Standard**: ORG-DEV-OTOI-1.0.0
**Repository**: NeuroLift-Technologies/rrt-advocate

---

## Purpose

This file defines how AI coding agents coordinate within this repository. All agents MUST read this file as Step 2 of the OTOI session start protocol (OTOI Section 4.1).

---

## Coordination Rules

1. **Check `docs/active-threads.md` before starting any work.** Do not duplicate or conflict with in-progress threads.
2. **Register yourself** using `templates/agent-registration.json` before making any commits.
3. **Commit with your name** in every commit: `[AGENT_NAME] type(scope): description`
4. **Write a handoff record** in `docs/agent-log/handoffs/` when ending a session with incomplete work.
5. **Escalate immediately** when scope is unclear, a blocker appears, or an architectural decision is needed.

---

## Internal File Map

| File | Purpose |
|---|---|
| `CLAUDE.md` | AI assistant guide — repo context, escalation, commit rules |
| `AGENTS.md` | This file — coordination protocol |
| `docs/active-threads.md` | Live work state — always check before starting |
| `docs/agent-log/registrations/` | Agent session registrations |
| `docs/agent-log/handoffs/` | Agent handoff records |
| `templates/agent-registration.json` | Self-registration template |
| `templates/handoff-record.json` | Handoff template |
| `templates/escalation.md` | Escalation template |
| `src/rrt_advocate.py` | Core engine — safety-critical, escalate before touching |
| `config/crisis_thresholds.yaml` | Crisis thresholds — safety-critical, escalate before touching |

---

## Guardrails

- **Never modify crisis intervention logic** without Joshua W. Dorsey, Sr.'s explicit approval
- **Never select or integrate LLM providers** without escalation
- **Never deploy to production** without escalation
- **Never approve governance amendments** — only Joshua can
- **Minimal footprint**: Only touch files necessary for your specific task

---

## Escalation Target

**Joshua W. Dorsey, Sr.**
Email: `info@neuroliftsolutions.com`
GitHub: `@JDUB1216`
Issue form: `.github/ISSUE_TEMPLATE/agent-escalation.md`
