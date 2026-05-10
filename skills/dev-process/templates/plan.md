# Plan — [task title]

References: **`artifacts.spec`**, **`artifacts.human_spec_gate`** — paths from `state.yaml` (prefixes reflect **creation order**, not semantic order).

## Review-depth preset and reasoning effort

| Field | Value |
|-------|-------|
| **Selected preset** | `light` / `standard` / `deep` — selection rules: `skills/dev-process/review/presets.md` |
| **Reasoning effort** | e.g. `default/medium` for `light` & `standard` (until escalated); `high` for `deep` on syntheses, blocker triage, architecture/impact; full table: `skills/dev-process/validation/SKILL.md` § Reasoning effort by review-depth preset |

If preset changes mid-task, record the escalation and reasoning change in **`artifacts.timeline`** when applicable.

## Model / reasoning audit

**Always fill this small block** (copied task plans break relative links—use plain paths below).

| Field | Value |
|-------|-------|
| **Audit required?** | yes / no |
| **Reason** | e.g. cost-sensitive / deep preset / high reasoning / human requested / no need |
| **Artifact** | If **yes**: bind `state.yaml` → `artifacts.model_usage`, materialize from template `skills/dev-process/templates/model_usage.md`, append rows as stages complete. If **no**: leave `artifacts.model_usage` empty unless policy changes mid-task. |

Set **Audit required?** to **yes** when any applies: preset is **`deep`**; **high** reasoning is used substantively; cost/usage must be accountable; human asked for audit; or **`artifacts.final_summary_ja`** must include **detailed per-session model evidence** beyond a short “audit not required” statement per plan.

**Exception:** preset **`deep`** (or **high** reasoning) usually implies **yes**, but the plan may instead state that **only final-summary-level** model/reasoning evidence is enough—then set **Audit required? no**, put that waiver in **Reason**, and skip **`artifacts.model_usage`** (detail: `skills/dev-process/validation/SKILL.md` section Model usage audit).

**Optional per-stage table** — fill **only** when **Audit required?** is **yes**:

| Stage | Preset | Main model expectation | Reasoning expectation | Evidence captured (redacted summaries only) |
|-------|--------|------------------------|----------------------|-----------------------------------------------|
| spec | | | | |
| spec review | | | | |
| plan | | | | |
| plan review | | | | |
| human spec gate | | | | |
| test | | | | |
| test review | | | | |
| implementation | | | | |
| final | | | | |

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

Which review targets/agents run after major milestones — router: `skills/dev-process/review/SKILL.md`.

## Test strategy

- Red-test expectation before implementation: [yes / no — justify if no, must align with spec]  
- Focused test paths / markers:  

## Escalation triggers (human)

Cross-check escalation triggers with `skills/dev-process/plan/SKILL.md` (API changes, architecture, scope creep, blocking reviews, etc.).
