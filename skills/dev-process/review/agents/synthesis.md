# Synthesis role (merge step, not an independent reviewer)

This file documents the **synthesis** step. It lives under `agents/` for discoverability beside review prompts, but **synthesis is not a reviewer “perspective”** like `architecture` or `requirements`.

Independent reviewers investigate the target fresh; synthesis **aggregates their written outputs**—de-duplicating, surfacing disagreement, and producing one recommendation—using [`../templates/synthesis_result.md`](../templates/synthesis_result.md).

Reviewer outputs must use [`../templates/review_result.md`](../templates/review_result.md). Do **not** use that template for synthesis; synthesis always fills **`synthesis.md`** via the synthesis template.

## Objective

Produce **one decisive summary** (`synthesis.md`) for the review stage without inventing findings that reviewers did not support.

## Rules

- De-duplicate findings; preserve unique evidence.  
- Prefer explicit **blocking** vs **non-blocking** tallies.  
- For **every blocking** finding when recommendation is not **Proceed**, fill the **6-column** table in [`../templates/synthesis_result.md`](../templates/synthesis_result.md): **Owner**, **Exact file/section**, **Required action**, **Re-review required** (plus ID source and summary). Owners: `spec` | `plan` | `test` | `implementation` | `artifact` | `human`.  
- Do **not** send all blockers to `implementation` by default; route per [review/SKILL.md § Rework routing](../SKILL.md#rework-routing).  
- State recommended action: proceed, rework plan, rework tests, stop for human—aligned with classifications.  
- Do not invent new technical findings; surface contradictions as **questions** for upstream stages or humans.

## Inputs

Typically all reviewer `*.md` files for the same stage (`requirements.md`, `architecture.md`, …), excluding draft synthesis.

## Output

Always write **`synthesis.md`** under **`reviews/<stage>/round_NN/`** for the **current** run using the synthesis template. **Never overwrite** prior `round_*` directories.

### You own `state.yaml` for this round (unless humans run everything by hand)

In the **same turn / session** as finishing `synthesis.md`, update the task’s **`state.yaml`**:

1. Set **`review_rounds.<stage>`** to **`NN`** (the integer encoded in `round_NN`, e.g. `round_02` → `2`).  
2. Set **`latest_reviews.<stage>`** to the path **`reviews/<stage>/round_NN/synthesis.md`** (relative to `.hermes/tasks/<task-id>/`).  
3. If and only if the recommendation **accepts** the stage (e.g. **Proceed**), set the matching **`reviewed.<key>: true`** per [templates/state.yaml](../../templates/state.yaml) mapping (`spec` / `plan` / `tests` / `final` only). Do **not** set `reviewed.*` on rework or blocking synthesis. **`implementation_phase`** reviews do not update `reviewed.*`.  
4. Do **not** set **`approved.*`**, **`pending_human_gate`**, or **`gate_prompted_at`**.

```text
reviewed.<key> is a review-pass marker, where <key> is one of the reviewed.* keys defined in templates/state.yaml.
Synthesis may set reviewed.<key>: true only when the review recommendation accepts the stage, such as Proceed.
Synthesis must not set approved.*, pending_human_gate, or gate_prompted_at.
```

Humans normally **do nothing** here. If synthesis was intentionally skipped this round per policy, **`state.yaml` is updated by the Orchestrator**, not skipped silently—see [review/SKILL.md § Who updates state.yaml](../SKILL.md#who-updates-stateyaml).

Optionally append a row to **`artifacts.timeline`** for “review synthesized / round NN” once state is consistent (or leave that to Orchestrator—avoid duplicate rows).
