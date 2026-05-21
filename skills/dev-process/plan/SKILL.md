---
name: dev-process-plan
description: >-
  Builds plan and phase_checklists artifacts from approved spec and human_spec_gate; runs plan review
  per review/SKILL.md; escalates to humans only on scope, API, architecture, or blocking review
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

- **`Selected review-depth preset`** for this task: `light`, `standard`, or `deep` — per [review/presets.md](../review/presets.md); restate escalation rule if preset may change mid-task (`standard → deep` when high-risk triggers appear).  
- **`Reasoning effort plan`** aligned with selected review-depth preset (Hermes-compatible: e.g. `/reasoning`): **`light`** — default/medium reasoning effort, high not used unless preset escalates; **`standard`** — default/medium reasoning effort unless escalated to `deep`; **`deep`** — high reasoning effort for syntheses, ambiguous blocker triage, architecture/impact, final recommendation ([validation/SKILL.md](../validation/SKILL.md#reasoning-effort-by-review-depth-preset)).  
- When plan is approved, set **`state.yaml` → `review_depth_preset`** to the same value as **Selected review-depth preset** (drives automatic profile/reasoning resolution via `model_policy.yaml`).
- **Session/model (v4):** Every role step is a **`run-dp` job** (`jobs.yaml` SOT); `run-dp render model-usage` produces the display table. All presets record jobs the same way ([validation/SKILL.md § v4 Job Contract](../validation/SKILL.md#v4-job-contract-canonical--new-tasks-only)).  
- **Session/model (pre-v4 only):** **`Model usage`** compact block in [templates/plan.md](../templates/plan.md) (`Model usage record required?` yes/no) — see template **Pre-v4** note. Review evidence via `review_manifest.yaml` ([review/SKILL.md § Pre-v4](../review/SKILL.md#pre-v4-review-round-session-evidence)).  
- Branch feasibility status checked before `human_spec_gate` and the task branch precondition (after plan review, before test implementation)  
- Implementation phases (small, ordered) — sized per [§ Implementation phase sizing](#implementation-phase-sizing); include a **Size** column in the plan table  
- Expected changed files per phase  
- Forbidden changes (what must not be touched), including **existing** git-untracked product/project files unless explicitly instructed; new product/test files the plan lists or clearly permits are allowed  
- Validation per phase (commands), including selected Python/Ruff commands for phases that touch Python code unless project policy overrides them  
- Rollback / stop conditions  
- Reviewer assignment notes (which review targets/agents later)  
- Test strategy (including when “red test before implementation” does not apply, e.g. docs-only)  

## Implementation phase sizing

Plan phases exist so **one ImplementationAgent `/goal` run** (within the configured Hermes **`agent.max_turns`** limit) can **implement, run that phase’s validation, and record `phase_results`** without hitting the iteration ceiling mid-work. Oversized phases are the main cause of half-finished product code and skipped validation.

**Do not over-split:** phases that already meet the **light** profile below need no further subdivision. Extra phases add review overhead without reducing agent risk.

### Light phase (keep as one phase; do not subdivide)

A phase is **light** when **all** apply:

- **At most one** product source file **or** only docs/examples/templates (no product code).  
- **At most three** ImplementationAgent checklist items (excluding validation recording).  
- Validation is **one or two** short commands (single linter path, single focused test file/module).  
- No new cross-module contracts **and** heavy parsing/rendering logic in the same phase.  

Examples: README tweak, single-field config addition with existing patterns, manifest field threaded through one call site.

### When to split (oversized)

Split into additional ordered phases when **any** trigger applies:

| Trigger | Guideline |
|---------|-----------|
| **Product file spread** | More than **two** product source files in one **implementation** phase (test-only phases may touch more test files — see below). |
| **Heavy modules combined** | Two or more “heavy” areas in one phase (e.g. large config parser + scene graph + pipeline/manifest). |
| **Checklist depth** | More than **eight** ImplementationAgent checklist items for one phase. |
| **New surface area** | More than **three** new public types/functions **across modules**, **or** one file gaining **more than five** new non-trivial helpers/parsers in one phase. |
| **Validation breadth** | Phase validation routinely runs **more than four** test modules **or** full-suite commands — narrow per-phase commands instead, or split phases. |
| **Subsystem mix** | Unrelated concerns bundled (schema/validation + IO output + runtime behavior) that can be validated independently. |
| **Agent budget** | PlanAgent judges the phase unlikely to finish implementation **and** phase validation within default `max_turns` even if other triggers are borderline. |

When splitting: renumber phases, duplicate the per-phase structure in **`artifacts.phase_checklists`**, narrow **allowed files** and **validation** per phase, and add one row per phase in the plan table. Prefer splits along **natural validation boundaries** (contracts → wiring → output), not arbitrary line counts.

### Test-authoring phases (RED / TestAuthorAgent)

Test-only phases may list **more than two** test files when the plan forbids product changes. Still split when:

- Distinct subsystems need separate RED waves (e.g. config schema vs pipeline/manifest), **or**  
- Checklist/validation would exceed the triggers above.

Do **not** split a test-only phase that only adds a **small** focused test module and one validation command.

### Plan table (required columns)

In **`artifacts.plan`**, the implementation table must include:

| Column | Content |
|--------|---------|
| **Phase** | Ordered id |
| **Objective** | One outcome |
| **Key files** | Expected touch set |
| **Size** | `light` / `medium` / `heavy` — `heavy` must not ship without split or documented waiver |
| **Split note** | `—` if `light`/`medium`; if `heavy`, either **split plan before review** or **waiver**: why one phase is still safe (rare; prefer split) |

`medium` = within caps but not trivial; still one `/goal` per phase at implementation time.

### Phase checklists alignment

**One checklist section per implementation phase** in **`artifacts.phase_checklists`**. Allowed files, forbidden changes, checklist items, and validation commands must match the plan row — no wider scope in checklists than in the plan.

Set `state.yaml` → `current_phase` to the active phase id (e.g. `2`, `2b`) when resuming so `/goal` does not rely on chat memory alone ([goal/SKILL.md](../goal/SKILL.md)).

### Plan review gate

Plan review ([review/SKILL.md](../review/SKILL.md), target `plan`) must treat an implementation phase marked **`heavy` without split or waiver** as **blocking** (`checklist_compliance` / `architecture`). `impact` should flag phases that combine public contract changes with wide file spread.

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
