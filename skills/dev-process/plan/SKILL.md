---
name: dev-process-plan
description: >-
  Builds plan.md and phase_checklists.md from approved spec and human_spec_gate; runs plan review
  via review router; escalates to humans only on scope, API, architecture, or blocking review
  findings. Use when planning implementation after spec gate, before test implementation.
---

# Plan stage

Turn an approved spec into an executable, reviewable plan. **There is no default human gate for plan**—use **agent review** and **escalate** only when needed.

## Inputs

- `.hermes/tasks/<task-id>/spec.md` (approved)  
- Latest approved spec synthesis, e.g. `.hermes/tasks/<task-id>/reviews/spec/round_NN/synthesis.md` (`state.yaml` → `latest_reviews.spec`)  
- `.hermes/tasks/<task-id>/human_spec_gate.md`  

## Outputs

- `.hermes/tasks/<task-id>/plan.md` — use [templates/plan.md](../templates/plan.md)  
- `.hermes/tasks/<task-id>/phase_checklists.md` — use [templates/phase_checklists.md](../templates/phase_checklists.md)  

After each plan review run, write outputs under `.hermes/tasks/<task-id>/reviews/plan/round_NN/` per orchestrator layout.

## Required content in `plan.md`

Include at minimum:

- Implementation phases (small, ordered)  
- Expected changed files per phase  
- Forbidden changes (what must not be touched)  
- Validation per phase (commands)  
- Rollback / stop conditions  
- Reviewer assignment notes (which review targets/agents later)  
- Test strategy (including when “red test before implementation” does not apply, e.g. docs-only)  

## Plan review

Run via [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `plan` → review agents `architecture`, `checklist_compliance`, `impact` → **synthesis:** yes (see [review/SKILL.md](../review/SKILL.md)).

## Hard rule before tests

```text
Do not start test implementation until plan review is complete.
If plan review has blocking findings or escalation triggers, stop.
```

## Human escalation (conditional)

Escalate to a human for approval or direction when **any** of the following is true:

- Public API or externally visible behavior will change.  
- Large architecture change.  
- Plan exceeds spec scope.  
- Plan appears to violate **forbidden changes** or spec constraints.  
- Plan claims tests cannot be written first and that claim is contested or weak.  
- Rollback / recovery looks impractical.  
- Any reviewer records a **blocking** finding in plan review.  

When escalating, document **reason** and update `plan.md` or task notes after resolution. Update [templates/state.yaml](../templates/state.yaml) fields `escalation.required` / `escalation.reason` if using that template.

## Permissions

Plan agents: **no** product code, **no** test code. Artifacts only.
