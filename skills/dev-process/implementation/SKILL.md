---
name: dev-process-implementation
description: >-
  Implements product code phase-by-phase against approved spec, plan, checklists, and tests;
  forbids modifying tests by default; stops and escalates test issues back to test stage. Use when
  writing production changes after independent test authoring in dev-process.
---

# Product implementation stage

Implement **approved** artifacts only:

- `spec.md`  
- `plan.md`  
- `phase_checklists.md`  
- Test outputs: `test_plan.md`, authored tests, latest test synthesis path in `state.yaml` → `latest_reviews.test` (and any mandated files your team tracks)  

## Branch precondition

Before `human_spec_gate`, the task should already have recorded whether a dedicated branch can be created for the task. Before product implementation starts, create or switch to that dedicated task branch after spec, plan, test authoring, and test review are complete. Follow repository branch policy first; otherwise use a stable task-related name such as `dev-process/<task-id>` or `feature/<short-task-slug>`. Do not start product implementation on `main`/`master` unless repository policy explicitly requires it. Product/project commits may happen only on a branch the agent created for the task; commits to other branches, merges, and pushes are forbidden unless explicitly requested. `.hermes/tasks/<task-id>/` remains uncommitted by default. Do not modify git-untracked product/project files without explicit human permission; if there is no instruction to modify an untracked file, leave it alone. Record branch status in `implementation_log.md` or `phase_results.md`.

## Phase execution

For each phase in `plan.md`:

1. Perform only scoped changes permitted by `phase_checklists.md`.  
2. Run phase validation commands (tests, linters), including the planned Python/Ruff command when the phase changes Python code.  
3. Append results to `.hermes/tasks/<task-id>/phase_results.md` using [templates/phase_results.md](../templates/phase_results.md).  
4. Run checkpoint review (see below).  
5. Proceed only if checkpoint is clear of blockers for the next phase.

Log ongoing narrative in [templates/implementation_log.md](../templates/implementation_log.md) at task root if useful.

## Checkpoint review (per phase)

Route via [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `implementation_phase` → review agents `checklist_compliance`, `diff_detail`, `architecture` → **synthesis:** optional per phase (see [review/SKILL.md](../review/SKILL.md)).

Write under `.hermes/tasks/<task-id>/reviews/implementation_phase_NN/round_MM/` (new `round_MM` per checkpoint review run).

## Rework after review

When review produces **blocking** findings, **do not** continue blindly. First **triage** (classification) happens in **`synthesis.md`** ([rework routing](../review/SKILL.md#rework-routing)); align with it here.

Typical sequence:

```text
review → finding triage (synthesis)
  → fix in the owning stage → run tests → rerun the needed review(s)
```

After each blocking-driven cycle, append **`rework_log.md`** and **`timeline.md`**, and write the **next** review under a **new** `reviews/<stage>/round_NN/` directory (see [review rounds](../review/SKILL.md#review-rounds-and-rework-history)).

### By root cause — where work returns

| Cause | Owner stage | Flow (high level) |
|-------|-------------|-------------------|
| **A. Product code** | ImplementationAgent | Fix product code → targeted tests → rerun checkpoint or final review. |
| **B. Test** | TestAuthorAgent / TestReviewerAgent | Fix tests → test review if needed → run tests → continue implementation or return to final review. **Not** ImplementationAgent editing tests. |
| **C. Plan** | PlanAgent | Revise plan → **plan review** → adjust tests if plan changed validation → return to implementation. |
| **D. Spec** | SpecAgent | Revise spec → spec review → **human spec gate** if material → **re-run plan onward** (plan, plan review, test stage as needed, then implementation). |

### ImplementationAgent may fix product code when findings are

Examples: product bugs, checklist gaps, missed work **inside the approved plan**, missing edge-case handling, **diff_detail**-style issues. Then: fix → targeted tests → rerun the relevant review.

**ImplementationAgent must not edit tests** to clear review or test failures except a **narrow, human-documented exception**.

### When tests are wrong (not product)

Examples: test does not match spec; brittle or overfit to implementation detail; wrong fixture/assertion; mismatch with planned validation commands. Route to **TestAuthorAgent → TestReviewerAgent → test checks** → only then ImplementationAgent / final review again.

See also [review/SKILL.md](../review/SKILL.md) (rework routing) and [test/SKILL.md](../test/SKILL.md) (test-failure triage).

## Test failure triage (during implementation)

Every **test failure** must be classified before fixing:

| Cause | Action |
|-------|--------|
| Product code defect | ImplementationAgent fixes product code (not tests). |
| Test defect / mismatch | Return to TestAuthorAgent / TestReviewerAgent. |
| Plan wrong or obsolete | Return to PlanAgent; rerun plan review; adjust downstream as needed. |
| Spec ambiguity or error | Return to SpecAgent; spec review; human spec gate if spec changes materially; re-run downstream stages. |

Never “make green” by **silently editing tests** as ImplementationAgent.

## Tests — default prohibition

```text
ImplementationAgent must not modify test files by default.
```

If implementation reveals tests are **wrong, obsolete, or incompatible** (imports, fixtures, assertions tied to invalid assumptions):

- **Stop** product work that depends on that ambiguity.  
- **Return** the task to **TestAuthorAgent / TestReviewer** with a clear description.  
- **Do not** silently rewrite tests so the implementation passes.

Minor mechanical fixes **still** flow through test agents unless humans explicitly waive separation for a narrowly scoped exception documented in-task.

## Forbidden patterns

- Out-of-plan refactors without plan amendment.  
- Widening scope to “clean up while here” without approval.  
- Editing tests without the test-role loop described above.

## Permissions

ImplementationAgent: **product code yes**; tests **no** by default.

## Validation gaps

If a Python-changing phase lacks a planned lint command and no project policy explains why, stop and return to PlanAgent rather than choosing an unreviewed Python environment or silently using unrelated system Python.

## If plan or tests appear wrong

**Stop** and escalate: adjust `plan.md` / `spec.md` via the proper upstream stages rather than improvising scope in code.
