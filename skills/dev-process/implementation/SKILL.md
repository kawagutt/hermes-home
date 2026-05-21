---
name: dev-process-implementation
description: >-
  Implements product code phase-by-phase against approved spec, plan, checklists, and tests;
  forbids modifying tests by default; stops and escalates test issues back to test stage. Use when
  writing production changes after independent test authoring in dev-process.
---

# Product implementation stage

Implement **approved** artifacts only:

- `artifacts.spec` (path from `state.yaml`)  
- `artifacts.plan`  
- `artifacts.phase_checklists`  
- Test outputs: **`artifacts.test_plan`**, authored tests, latest test synthesis path in `state.yaml` → `latest_reviews.test` (and any mandated files your team tracks)  

## Task branch precondition

Before `human_spec_gate`, the task should already have recorded branch feasibility (whether dev-process can create a dedicated branch for this task, or the human must explicitly direct branch choice).

Before **test implementation** starts, create or switch to the dedicated task branch **dev-process created for this task** (Orchestrator may create/switch; see [git/SKILL.md](../git/SKILL.md) and orchestrator [SKILL.md](../SKILL.md) role table). **Test authoring, test review, and product implementation** all happen on that task branch. Do not defer branch creation until after the test stage.

Do not use any pre-existing branch for task work unless the human **explicitly** instructs it. Product and test commits may happen **only** on the dev-process-created task branch; commits to other branches, merges, and pushes are forbidden unless explicitly requested. `.hermes/tasks/<task-id>/` remains uncommitted by default. Do not modify **existing** git-untracked product/project files unless explicitly instructed. Creating **new** product files allowed by the approved plan is permitted. Task artifacts under `.hermes/tasks/<task-id>/` are exempt from the untracked-product rule but remain uncommitted by default. Record branch status in **`artifacts.implementation_log`** or **`artifacts.phase_results`** (paths from `state.yaml`).

## Phase execution

Each phase must fit the sizing rules in [plan/SKILL.md § Implementation phase sizing](../plan/SKILL.md#implementation-phase-sizing). One bounded `/goal` advance should complete **at most one** implementation phase (implement → validate → `phase_results` → checkpoint review) before starting the next.

For each phase in **`artifacts.plan`**:

1. Perform only scoped changes permitted by **`artifacts.phase_checklists`**.  
2. Run phase validation commands (tests, linters), including the planned Python/Ruff command when the phase changes Python code.  
3. Append results to `.hermes/tasks/<task-id>/` + **`artifacts.phase_results`** using [templates/phase_results.md](../templates/phase_results.md).  
4. Run checkpoint review (see below).  
5. Proceed only if checkpoint is clear of blockers for the next phase.

Log ongoing narrative in [templates/implementation_log.md](../templates/implementation_log.md) at task root if useful.

## Checkpoint review (per phase)

Route via [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `implementation_phase` → review agents `checklist_compliance`, `diff_detail`, `architecture` → **synthesis:** optional per phase (see [review/SKILL.md](../review/SKILL.md)).

Write under `.hermes/tasks/<task-id>/reviews/implementation_phase_NN/round_MM/` (new `round_MM` per checkpoint review run).

**Session evidence:** Checkpoint review workers and synthesis → [review/SKILL.md § Review round session evidence](../review/SKILL.md#review-round-session-evidence-completion) (`review_manifest.yaml` only). After each implementation **phase** primary work segment, append an **`implementation_phase_NN`** row to **`artifacts.model_usage`** per [validation/SKILL.md § Primary segment boundary completion](../validation/SKILL.md#primary-segment-boundary-completion) when **`model_usage_required`** is true. Do not advance to the next phase until required evidence for the completed segment is recorded.

## Rework after review

When review produces **blocking** findings, **do not** continue blindly. First **triage** (classification) happens in the round’s **`synthesis.md`** ([rework routing](../review/SKILL.md#rework-routing)); align with it here.

Typical sequence:

```text
review → finding triage (synthesis)
  → fix in the owning stage → run tests → rerun the needed review(s)
```

After each blocking-driven cycle, append **`artifacts.rework_log`** and **`artifacts.timeline`**, and write the **next** review under a **new** `reviews/<stage>/round_NN/` directory (see [review rounds](../review/SKILL.md#review-rounds-and-rework-history)).

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

**Stop** and escalate: adjust **`artifacts.plan`** / **`artifacts.spec`** via the proper upstream stages rather than improvising scope in code.
