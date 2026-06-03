# Escalation Notice

**Governance Standard**: ORG-DEV-OTOI-1.0.0
**Repository**: NeuroLift-Technologies/rrt-advocate
**Escalation Target**: Joshua W. Dorsey, Sr. (`info@neuroliftsolutions.com`)

---

**Agent**: CODEX
**Session ID**: CODEX-2026-06-02-governance-session-docs
**Date**: 2026-06-02
**Branch**: `codex/governance-session-docs`

## Escalation Trigger (OTOI Section 8)

- [x] Architectural or deployment decision required
- [ ] Blocker cannot be resolved by agent alone
- [x] Ethical concern
- [x] LLM provider or external service integration needed
- [ ] Production deployment being considered
- [ ] Governance document amendment proposed
- [x] Safety-critical code change (crisis intervention logic)

## Description

During prior PR #25 work, Codex did not complete the repository's required governance entry protocol before creating and updating the RRT AIdvocAIte Worker chat PR. The work included a Cloudflare Workers AI path and a crisis-adjacent change to behavioral token hashing in `src/crisis/detectors/behavioral_layer.py`.

Although the PR checks and reviewer comments were addressed technically, the process was not fully OTOI-compliant. This escalation notice records that gap and flags the decisions that still require Joshua's explicit approval before merge.

## Context

- PR #25: `[CODEX] feat(assistant): add RRT AIdvocAIte Worker chat`
- Branch: `codex/rrt-aidvocaite-integration-v2`
- Relevant governance:
  - `AGENTS.md` requires reading `NLT-DEV-OTOI.md`, `CLAUDE.md`, and `docs/active-threads.md`, then self-registering and confirming scope before significant work.
  - `CLAUDE.md` states this is a safety-critical system and that changes touching crisis detection logic, persona blending, safety thresholds, architecture, deployment, LLM provider choice, or external service integration require escalation to Joshua.

## Requested Decision

Joshua should decide whether PR #25 may proceed as the implementation direction for the website/app, whether the Cloudflare Workers AI path is approved for this repo, and whether the behavioral token hashing change is acceptable in the crisis-adjacent code path.

## Work State

This documentation PR adds the missing session records and escalation notice only. It does not change application behavior. PR #25 remains separate and must not be merged without Joshua's approval.
