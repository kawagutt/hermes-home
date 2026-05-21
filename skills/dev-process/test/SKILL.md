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
- **Task branch precondition** is satisfied: the dedicated task branch dev-process uses for this task exists, the working tree is on it, `branch.task_branch_precondition_met` is true, and `state.yaml` → `branch` matches the canonical branch rule in [git/SKILL.md](../git/SKILL.md) / orchestrator [SKILL.md](../SKILL.md) (so test files and later product files are authored on the same task branch; a pre-existing branch **only** if the human explicitly instructed it and it is recorded in `feasibility_notes`).

If any precondition fails, **stop**—do not author tests yet.

## Agents

- **TestAuthorAgent** writes and updates **test code** only.  
- **TestReviewerAgent** is read-only on product and test code except review artifacts.

**ImplementationAgent must not author tests** in this phase.

## Allowed context for TestAuthor

Use:

- Approved **`artifacts.spec`** and **`artifacts.plan`** (paths from `state.yaml`)  
- **`artifacts.phase_checklists`** validation expectations (path from `state.yaml`)  
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
| `artifacts.test_plan` | [templates/test_plan.md](../templates/test_plan.md) |
| Test code | repo test layout |
| `artifacts.test_implementation` | [templates/test_implementation.md](../templates/test_implementation.md) |
| `artifacts.red_test_result` | [templates/red_test_result.md](../templates/red_test_result.md) (or a clearly marked **Red test results** section inside **`artifacts.test_implementation`** during the test stage only) |
| Review outputs | `.hermes/tasks/<task-id>/reviews/test/round_NN/` |

## Red / validation policy

When feasible, run tests **before** product implementation so they fail (“red”) for the right reasons, then ImplementationAgent makes them pass.

If red tests are inappropriate (documentation-only cleanup, refactor with no behavior change planned, etc.), the exception **must already be justified in `artifacts.plan`**. Substitute verification (review, links, commands) per plan.

## Test review

Use [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `test` → review agents `requirements`, `test_quality`, `checklist_compliance` → **synthesis:** yes (see [review/SKILL.md](../review/SKILL.md)).

**Session evidence:** Test review rounds → [review/SKILL.md § Review round session evidence](../review/SKILL.md#review-round-session-evidence-completion). When **`model_usage_required`** is true, after the test **primary** segment (test authoring) completes, record its boundary row in **`artifacts.model_usage`** with `--stage-id test` per [validation/SKILL.md § Primary segment boundary completion](../validation/SKILL.md#primary-segment-boundary-completion) before treating test work as governance-complete for that segment.

Blocking findings → **do not** start ImplementationAgent until resolved via test revisions or explicit spec/plan amendment loop.

If test review clears and `state.yaml` / latest synthesis permit it, the next legal stage is **product implementation**.

Because this crosses into the ImplementationAgent role, continue only by an **explicit role transition** that states:

- new role: `ImplementationAgent`;
- allowed scope from `plan.md` / `phase_checklists`;
- approved inputs and latest review pointers;
- test files are not to be modified by ImplementationAgent by default.

Do not silently change role inside the same `/goal` loop.

Do not stop merely because the test stage boundary or role boundary was reached. Stop only if continuing would be unsafe, illegal, missing required context/tools, or blocked by gate/escalation/review findings.

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

TestAuthorAgent: **tests only**, no production/product source changes; may **commit** test changes only on the dev-process-created task branch (see [SKILL.md](../SKILL.md) role table); no merge/push.
