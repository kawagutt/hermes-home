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
- Test outputs: `test_plan.md`, authored tests, `reviews/test/` synthesis (and any mandated files your team tracks)  

## Phase execution

For each phase in `plan.md`:

1. Perform only scoped changes permitted by `phase_checklists.md`.  
2. Run phase validation commands (tests, linters).  
3. Append results to `.hermes/tasks/<task-id>/phase_results.md` using [templates/phase_results.md](../templates/phase_results.md).  
4. Run checkpoint review (see below).  
5. Proceed only if checkpoint is clear of blockers for the next phase.

Log ongoing narrative in [templates/implementation_log.md](../templates/implementation_log.md) at task root if useful.

## Checkpoint review (per phase)

Route via [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `implementation_phase` → review agents `checklist_compliance`, `diff_detail`, `architecture` → **synthesis:** optional per phase (see [review/SKILL.md](../review/SKILL.md)).

Write under `.hermes/tasks/<task-id>/reviews/implementation_phase_NN/`.

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

## If plan or tests appear wrong

**Stop** and escalate: adjust `plan.md` / `spec.md` via the proper upstream stages rather than improvising scope in code.
