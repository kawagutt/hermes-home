# Synthesis role (merge step, not an independent reviewer)

This file documents the **synthesis** step. It lives under `agents/` for discoverability beside review prompts, but **synthesis is not a reviewer “perspective”** like `architecture` or `requirements`.

Independent reviewers investigate the target fresh; synthesis **aggregates their written outputs**—de-duplicating, surfacing disagreement, and producing one recommendation—using [`../templates/synthesis_result.md`](../templates/synthesis_result.md).

Reviewer outputs must use [`../templates/review_result.md`](../templates/review_result.md). Do **not** use that template for synthesis; synthesis always fills `synthesis.md` via the synthesis template.

## Objective

Produce **one decisive summary** (`synthesis.md`) for the review stage without inventing findings that reviewers did not support.

## Rules

- De-duplicate findings; preserve unique evidence.  
- Prefer explicit **blocking** vs **non-blocking** tallies.  
- State recommended action: proceed, rework plan, rework tests, stop for human—aligned with classifications.  
- Do not invent new technical findings; surface contradictions as **questions** for upstream stages or humans.

## Inputs

Typically all reviewer `*.md` files for the same stage (`requirements.md`, `architecture.md`, …), excluding draft synthesis.

## Output

Always write **`synthesis.md`** for that stage using the synthesis template.
