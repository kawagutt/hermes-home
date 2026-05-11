# Plan — [task title]

References: **`artifacts.spec`**, **`artifacts.human_spec_gate`** — paths from `state.yaml` (prefixes reflect **creation order**, not semantic order).

## Review-depth preset and reasoning effort

| Field | Value |
|-------|-------|
| **Selected review-depth preset** | `light` / `standard` / `deep` — selection rules: `skills/dev-process/review/presets.md` |
| **Reasoning effort** | e.g. `default/medium` reasoning effort for `light` & `standard` (until escalated); `high` reasoning effort for `deep` on syntheses, blocker triage, architecture/impact; full table: `skills/dev-process/validation/SKILL.md` § Reasoning effort by review-depth preset |

If preset changes mid-task, record the escalation and reasoning change in **`artifacts.timeline`** when applicable.

## Model usage

**Always fill this small block** (copied task plans break relative links—use plain paths below).

| Field | Value |
|-------|-------|
| **Model usage record required?** | yes / no |
| **Reason** | e.g. cost-sensitive / deep preset / high reasoning effort / human requested / no need |
| **Artifact** | If **yes**: bind `state.yaml` → `artifacts.model_usage`, materialize from template `skills/dev-process/templates/model_usage.md`, append rows as stages complete. If **no**: leave `artifacts.model_usage` empty unless policy changes mid-task. |

Set **`Model usage record required?`** to **yes** when any applies: preset is **`standard`** or **`deep`**; **high** reasoning effort is used for primary-loop work, not only shallow side tasks; cost/usage must be accountable; human asked for **detailed model usage records**; or **`artifacts.final_summary_ja`** should carry **stage-attributed model evidence** (see **`artifacts.model_usage`**).

**Default policy (`dev-process`):** Tasks on preset **`standard`** or **`deep`** MUST set **`Model usage record required?`** to **yes**, bind **`artifacts.model_usage`**, materialize from `skills/dev-process/templates/model_usage.md`, and **append rows** at major stage boundaries (see `skills/dev-process/validation/SKILL.md` § Model usage). Preset **`light`** or **trivial docs-only / mechanical tasks** MAY set **`no`** with **Reason** `no need` and leave **`artifacts.model_usage`** empty. A **`standard`** or **`deep`** plan that sets **`no`** MUST document **explicit human approval** for skipping **`artifacts.model_usage`** (copied rationale in **Reason** plus a pointer such as **`artifacts.timeline`**)—silent waivers are **non-compliant**.

**Optional per-stage table** — fill **only** when **`Model usage record required?`** is **yes**. Stage ids align with **`state.yaml`** (`current_stage`, `review_rounds` keys such as `spec` / `plan` / `test` / `final`), **`reviews/<stage>/`**, **`artifacts.human_spec_gate`**, and `skills/dev-process/templates/model_usage.md`:

| Stage id | Selected review-depth preset | Main model expectation | Reasoning effort expectation | Evidence captured (redacted summaries only) |
|----------|------------------------------|------------------------|-----------------------------|---------------------------------------------|
| `spec` | | | | |
| `spec_review` | | | | |
| `human_spec_gate` | | | | |
| `plan` | | | | |
| `plan_review` | | | | |
| `test` | | | | |
| `test_review` | | | | |
| `implementation` | | | | |
| `implementation_review` | | | | |
| `final_review` | | | | |
| `final_summary` | | | | |
| `final_human_gate` | | | | |

## Implementation phases

| Phase | Objective | Key files (expected) |
|-------|-----------|----------------------|
| 1 | | |
| 2 | | |

## Forbidden changes

- 

## Validation per phase

| Phase | Commands | Notes |
|-------|----------|-------|
| 1 | | |

## Rollback / stop conditions

- 

## Reviewer assignment notes

Which review targets/agents run after major milestones — **See:** `skills/dev-process/review/SKILL.md`.

## Test strategy

- Red-test expectation before implementation: [yes / no — justify if no, must align with spec]  
- Focused test paths / markers:  

## Escalation triggers (human)

Cross-check escalation triggers with `skills/dev-process/plan/SKILL.md` (API changes, architecture, scope creep, blocking reviews, etc.).
