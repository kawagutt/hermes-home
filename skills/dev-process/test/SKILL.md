---
name: dev-process-test
description: >-
  Authors tests after plan review from spec and plan only (TestAuthorAgent); records test_plan and
  red/validation results; runs test review. No product code edits. Use when executing the test
  phase before product implementation in dev-process.
---

# Test stage (independent of product implementation)

Tests are **not** a sub-step of implementation. They are a **separate phase** after **plan review** and **before** ImplementationAgent changes product code.

## Preconditions

- Plan review is **complete**.  
- No **blocking** plan review findings remain unaddressed.  
- Any **escalation** required by plan review is **resolved** (see [plan/SKILL.md](../plan/SKILL.md)).  

If any precondition fails, **stop**—do not author tests yet.

## Agents

- **TestAuthorAgent** writes and updates **test code** only.  
- **TestReviewerAgent** is read-only on product and test code except review artifacts.

**ImplementationAgent must not author tests** in this phase.

## Allowed context for TestAuthor

Use:

- Approved `spec.md` and `plan.md`  
- `phase_checklists.md` validation expectations  
- Relevant **existing tests** (style, helpers)  
- Relevant **public APIs** / interfaces under test  

Avoid:

- ImplementationAgent scratch notes  
- Unapproved product diffs  
- “How we will implement” rationale unless it is already in approved plan/spec  

## Outputs

Suggested task files (adapt names to repo conventions):

| Artifact | Template |
|---------|----------|
| `test_plan.md` | [templates/test_plan.md](../templates/test_plan.md) |
| Test code | repo test layout |
| `test_implementation.md` | [templates/test_implementation.md](../templates/test_implementation.md) |
| `red_test_result.md` | [templates/red_test_result.md](../templates/red_test_result.md) (or a clearly marked **Red test results** section inside `test_implementation.md` during the test stage only) |
| Review outputs | `.hermes/tasks/<task-id>/reviews/test/` |

## Red / validation policy

When feasible, run tests **before** product implementation so they fail (“red”) for the right reasons, then ImplementationAgent makes them pass.

If red tests are inappropriate (documentation-only cleanup, refactor with no behavior change planned, etc.), the exception **must already be justified in `plan.md`**. Substitute verification (review, links, commands) per plan.

## Test review

Use [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `test` → review agents `requirements`, `test_quality`, `checklist_compliance` → **synthesis:** yes (see [review/SKILL.md](../review/SKILL.md)).

Blocking findings → **do not** start ImplementationAgent until resolved via test revisions or explicit spec/plan amendment loop.

## Test failure triage (after implementation has started)

When tests fail **during or after** product implementation, **every** failure is triaged before anyone edits code:

| Cause | Who acts |
|-------|----------|
| Product defect | ImplementationAgent fixes **product** code only. |
| Test wrong / brittle / misaligned | TestAuthorAgent / TestReviewerAgent (not ImplementationAgent). |
| Plan wrong | PlanAgent → plan review → downstream updates. |
| Spec wrong or ambiguous | SpecAgent → spec review → human spec gate if material → re-run downstream. |

Full detail: [implementation/SKILL.md](../implementation/SKILL.md) (Test failure triage, Rework after review). Synthesis **rework owner** rules: [review/SKILL.md](../review/SKILL.md#rework-routing).

## Permissions

TestAuthorAgent: **tests only**, no production/product source changes.
