# CLAUDE.md — AI Assistant Guide for `rrt-advocate`

**Repository**: NeuroLift-Technologies/rrt-advocate
**Purpose**: Rapid Response Team Advocate — Crisis intervention and immediate ADHD support agent within the NeuroLift HAIEF Solidarity Framework
**Governance Standard**: ORG-DEV-OTOI-1.0.0
**Last Updated**: 2026-04-04
**Intended Audience**: Claude, Claude Code, Copilot, Cursor, Gemini, and all AI coding agents

---

## EXECUTIVE SUMMARY

You are working in the **rrt-advocate** repository. This agent is the **Protective Layer** of the NeuroLift Human-AI ElevAItion Foundation (HAIEF) Solidarity Framework. It handles acute crisis intervention, immediate ADHD support, and rapid-response emotional scaffolding for neurodivergent users.

**This is a safety-critical system.** Crisis intervention logic must never be modified without explicit approval from Joshua W. Dorsey, Sr.

**Mission**: Provide immediate, shame-resistant, trauma-informed crisis support while preserving user agency and privacy at all times.

---

## MANDATORY GOVERNANCE CONTRACT

This repository operates under **ORG-DEV-OTOI-1.0.0**.

Before beginning any work, you MUST complete the 5-step session start protocol:

1. Read `NLT-DEV-OTOI.md` in `.github-private` (Sections 1, 4, 4.4, 5, 8)
2. Read `AGENTS.md` in this repository
3. Read this file (`CLAUDE.md`) — you are here ✓
4. Read `docs/active-threads.md` — check for in-progress work before starting
5. Complete `templates/agent-registration.json` and confirm scope with Joshua

**Commit Format (OTOI Section 4.4)**:
```
[AGENT_NAME] type(scope): description
```
Valid types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `ci`

Example: `[CLAUDE] chore(governance): add OTOI governance scaffolding (ORG-DEV-OTOI-1.0.0)`

---

## ESCALATION — MANDATORY READ

**Escalate to Joshua W. Dorsey, Sr. (`info@neuroliftsolutions.com`) IMMEDIATELY if:**

- The task scope is unclear or conflicts with existing work in `docs/active-threads.md`
- Any change touches crisis detection logic, persona blending, or safety thresholds
- An architectural or deployment decision is required
- A blocker cannot be resolved by the agent alone
- An ethical concern arises (this is a safety-critical mental health system)
- An LLM provider or external service integration is needed
- A production deployment is being considered
- A governance document amendment is proposed

Use `.github/ISSUE_TEMPLATE/agent-escalation.md` to file escalations as GitHub issues.

**Never make architectural decisions unilaterally in this repo.**

---

## REPOSITORY STRUCTURE

```
rrt-advocate/
├── src/
│   └── rrt_advocate.py          # Core crisis intervention engine
├── config/
│   └── crisis_thresholds.yaml   # Crisis detection thresholds (safety-critical)
├── docs/
│   ├── integration_guide.md     # Integration documentation
│   ├── active-threads.md        # ⚠️ Active work tracker — READ BEFORE STARTING
│   └── agent-log/               # Agent session records
│       ├── registrations/       # Agent self-registration files
│       └── handoffs/            # Agent handoff records
├── templates/
│   ├── agent-registration.json  # Template: agent self-registration
│   ├── handoff-record.json      # Template: session handoffs
│   ├── escalation.md            # Template: escalation notices
│   └── intent-log.md            # Template: intent tracking
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── agent-escalation.md  # File escalations here
│       └── governance-proposal.md
├── .nltotoi/
│   ├── index/governance-files.md
│   └── scripts/validate-governance.sh
├── GEMINI_TOPOGRAPHY.py         # Repo navigation guide (all AI agents read this)
├── CLAUDE.md                    # This file
├── AGENTS.md                    # Agent coordination protocol
└── README.md                    # Project overview
```

---

## CORE PRINCIPLES (Non-Negotiable)

1. **User Safety First** — Crisis intervention logic is safety-critical; no unilateral changes
2. **Shame-Resistant Design** — No language that implies failure or blame
3. **Privacy-First** — User data stays local; no external transmission without consent
4. **User Agency** — The user is always in control; AI supports, never overrides
5. **Neurodivergent-by-Design** — Built for ADHD and neurodivergent cognitive profiles

---

## TECHNOLOGY STACK

- **Python 3.8+**: Core implementation language
- **YAML**: Configuration (`config/crisis_thresholds.yaml`)
- **JSON**: Templates and agent records
- **Markdown**: Documentation

---

## WORKING WITH JOSHUA (Repository Authority)

**Authority**: Joshua W. Dorsey, Sr. — sole approver for architectural decisions, governance amendments, and production deployments.

**Contact**: `info@neuroliftsolutions.com`

**Collaboration style**:
- Direct and structured communication
- Present 2-3 options with tradeoffs — never prescribe a single path
- Connect work to mission impact
- Respect ADHD working style: multi-threaded, interest-driven, parallel threads are normal
- Your role: implement the vision, not define it

---

## WHAT NOT TO DO

- ❌ Do not merge or modify architectural PRs without Joshua's explicit sign-off
- ❌ Do not modify `config/crisis_thresholds.yaml` without escalation
- ❌ Do not store user crisis data in any persistent external system
- ❌ Do not select or integrate LLM providers unilaterally
- ❌ Do not make commits without the `[AGENT_NAME]` prefix
- ❌ Do not start work without checking `docs/active-threads.md`

---

## QUICK REFERENCE

| Need | Where to go |
|---|---|
| Governance contract | `NLT-DEV-OTOI.md` in `.github-private` |
| Active work state | `docs/active-threads.md` |
| Self-registration | `templates/agent-registration.json` |
| File an escalation | `.github/ISSUE_TEMPLATE/agent-escalation.md` |
| Propose governance change | `.github/ISSUE_TEMPLATE/governance-proposal.md` |
| Validate compliance | `.nltotoi/scripts/validate-governance.sh` |
