---
name: dev-process-review
description: >-
  Routes independent reviews by combining a target (what to review) with agents (perspective) and
  shared output templates. Defines blocking vs non-blocking findings and synthesis rules. Does not
  contain per-reviewer checklists—those live in targets/ and agents/. Use when assigning reviews in
  dev-process.
---

# Review process (router)

Reviews are assembled from three pieces:

1. A **target** from [`targets/`](targets/) — defines *what* is in scope.  
2. One or more **agents** from [`agents/`](agents/) — defines *how* to look at it.  
3. Output shape from [`templates/review_result.md`](templates/review_result.md) and [`templates/synthesis_result.md`](templates/synthesis_result.md).

`review/targets/*.md` and `review/agents/*.md` are **reference prompt fragments**, not standalone skills. This file is the **router** only: **recipes + contract**, not detailed checklists.

## Findings classification

Each reviewer labels items as one of:

- **blocking** — must fix or re-scope before advancing.  
- **non-blocking** — should fix soon; documented technical debt acceptable with rationale.  
- **question** — needs author or human clarification.  
- **suggested follow-up** — optional improvement.  

## Context isolation

- Do not attach ImplementationAgent conversational rationale unless explicitly requested.  
- Prefer approved artifacts, concise diffs, test outputs, and prior review summaries.  

## Synthesis

A **synthesis** step merges independent reviewer files into one recommendation (`synthesis.md`) using [`templates/synthesis_result.md`](templates/synthesis_result.md). It should resolve duplicated findings and state **merge/readiness**.

Synthesis **per implementation phase** may be skipped for cost; final synthesis should not be skipped arbitrarily when merge decisions matter.

---

## Standard recipes (combinations only)

These lines name targets and agents. **Detailed bullets stay in agent files.**

### Spec review

- **target:** `spec` (`targets/spec.md`)  
- **agents:** `requirements`, `architecture`, `synthesis`

### Plan review

- **target:** `plan` (`targets/plan.md`)  
- **agents:** `architecture`, `checklist_compliance`, `impact`, `synthesis`

### Test review

- **target:** `test` (`targets/test.md`)  
- **agents:** `requirements`, `test_quality`, `checklist_compliance`, `synthesis`

### Implementation phase checkpoint

- **target:** `implementation_phase` (`targets/implementation_phase.md`)  
- **agents:** `checklist_compliance`, `diff_detail`, `architecture`, optional `synthesis`

### Final review

- **target:** `final_diff` (`targets/final_diff.md`)  
- **agents:** `architecture`, `diff_detail`, `impact`, `naming_doc`, `test_quality`, `synthesis`

---

## Task output locations

Mirror recipes under `.hermes/tasks/<task-id>/reviews/` as documented in the orchestrator [`SKILL.md`](../SKILL.md).
