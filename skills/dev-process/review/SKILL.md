---
name: dev-process-review
description: >-
  Routes independent reviews by combining a target (what to review) with agents (perspective) and
  shared output templates. Defines blocking vs non-blocking findings and synthesis rules. Does not
  contain per-reviewer checklists—those live in targets/ and agents/. Use when assigning reviews in
  dev-process.
---

# Review process (router)

Reviews combine:

1. A **target** from [`targets/`](targets/) — defines *what* is in scope.  
2. One or more **independent review agents** (prompts under [`agents/`](agents/) *except* [`synthesis.md`](agents/synthesis.md)) — *how* to look at the target from each perspective.  
3. Shared **output format** per reviewer via [`templates/review_result.md`](templates/review_result.md).  

After reviewers finish, optionally run a **synthesis role** ([`agents/synthesis.md`](agents/synthesis.md)) that merges their outputs using [`templates/synthesis_result.md`](templates/synthesis_result.md) → `synthesis.md`. **Synthesis is not another independent reviewer agent**—it aggregates reviewer outputs without inventing new primary findings.

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

Recipes name **targets** and **review agents** only. **Synthesis** is a separate line (merge step). **Detailed bullets stay in agent files.**

### Spec review

- **target:** `spec` (`targets/spec.md`)  
- **review agents:** `requirements`, `architecture`  
- **synthesis:** yes  

### Plan review

- **target:** `plan` (`targets/plan.md`)  
- **review agents:** `architecture`, `checklist_compliance`, `impact`  
- **synthesis:** yes  

### Test review

- **target:** `test` (`targets/test.md`)  
- **review agents:** `requirements`, `test_quality`, `checklist_compliance`  
- **synthesis:** yes  

### Implementation phase checkpoint

- **target:** `implementation_phase` (`targets/implementation_phase.md`)  
- **review agents:** `checklist_compliance`, `diff_detail`, `architecture`  
- **synthesis:** optional (skip for cheap phases if team policy allows)  

### Final review

- **target:** `final_diff` (`targets/final_diff.md`)  
- **review agents:** `architecture`, `diff_detail`, `impact`, `naming_doc`, `test_quality`  
- **synthesis:** required  

---

## Task output locations

Mirror recipes under `.hermes/tasks/<task-id>/reviews/` as documented in the orchestrator [`SKILL.md`](../SKILL.md).
