---
name: dev-process-plan
description: >-
  Builds plan and phase_checklists artifacts from approved spec and human_spec_gate; runs plan review
  via review router; escalates to humans only on scope, API, architecture, or blocking review
  findings. Use when planning implementation after spec gate, before test implementation.
---

# Plan stage

Turn an approved spec into an executable, reviewable plan. **There is no default human gate for plan**—use **agent review** and **escalate** only when needed.

## Inputs

- `.hermes/tasks/<task-id>/` + `artifacts.spec` — approved  
- Latest approved spec synthesis, e.g. `.hermes/tasks/<task-id>/reviews/spec/round_NN/synthesis.md` (`state.yaml` → `latest_reviews.spec`)  
- `.hermes/tasks/<task-id>/` + `artifacts.human_spec_gate`  

## Outputs

- `.hermes/tasks/<task-id>/` + `artifacts.plan` — use [templates/plan.md](../templates/plan.md)  
- `.hermes/tasks/<task-id>/` + `artifacts.phase_checklists` — use [templates/phase_checklists.md](../templates/phase_checklists.md)  

After each plan review run, write outputs under `.hermes/tasks/<task-id>/reviews/plan/round_NN/` per [artifacts/SKILL.md — Review outputs by stage](../artifacts/SKILL.md#review-outputs-by-stage).

## Required content in the plan artifact (`artifacts.plan`; path from `state.yaml`)

Include at minimum:

- Branch feasibility status checked before `human_spec_gate` and the task branch precondition (after plan review, before test implementation)  
- Implementation phases (small, ordered)  
- Expected changed files per phase  
- Forbidden changes (what must not be touched), including **existing** git-untracked product/project files unless explicitly instructed; new product/test files the plan lists or clearly permits are allowed  
- Validation per phase (commands), including selected Python/Ruff commands for phases that touch Python code unless project policy overrides them  
- Rollback / stop conditions  
- Reviewer assignment notes (which review targets/agents later)  
- Test strategy (including when “red test before implementation” does not apply, e.g. docs-only)  


## Validation environment policy

PlanAgent owns validation selection. Use this precedence:

1. User-explicit validation commands.
2. Project docs/config such as `AGENTS.md`, README, Makefile, `pyproject.toml`, or equivalent.
3. Dev-process defaults from [../validation/SKILL.md](../validation/SKILL.md#cost-aware-validation-and-model-use).

For Python code changes, include a Ruff validation command in **`artifacts.phase_checklists`** unless the project explicitly uses another linting policy. Prefer touched Python paths first. If no project rule exists, prefer `uv run ruff check <touched-python-paths>` or `.venv/bin/python -m ruff check <touched-python-paths>` when appropriate. Do not leave Python lint policy for ImplementationAgent to invent ad hoc.

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

When escalating, document **reason** and update **`artifacts.plan`** or task notes after resolution. Update [templates/state.yaml](../templates/state.yaml) fields `escalation.required` / `escalation.reason` if using that template.

## Permissions

Plan agents: **no** product code, **no** test code. Artifacts only.
