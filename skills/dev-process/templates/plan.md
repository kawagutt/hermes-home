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

When the plan is approved, also set **`state.yaml` → `model_usage_required`** to `true` or `false` (same answer as the table) so validators need not rely on Markdown parsing alone.

Set **`Model usage record required?`** to **yes** when any applies: preset is **`standard`** or **`deep`**; **high** reasoning effort is used for primary-loop work, not only shallow side tasks; cost/usage must be accountable; human asked for **detailed model usage records**; or **`artifacts.final_summary_ja`** should carry **stage-attributed model evidence** (see **`artifacts.model_usage`**).

**Default policy (`dev-process`):** Tasks on preset **`standard`** or **`deep`** MUST set **`Model usage record required?`** to **yes**, bind **`artifacts.model_usage`**, materialize from `skills/dev-process/templates/model_usage.md`, and **append rows** at major stage boundaries (see `skills/dev-process/validation/SKILL.md` § Model usage). Preset **`light`** or **trivial docs-only / mechanical tasks** MAY set **`no`** with **Reason** `no need` and leave **`artifacts.model_usage`** empty. A **`standard`** or **`deep`** plan that sets **`no`** MUST document **explicit human approval** for skipping **`artifacts.model_usage`** (copied rationale in **Reason** plus a pointer such as **`artifacts.timeline`**)—silent waivers are **non-compliant**.

**Optional per-stage table** — fill **only** when **`Model usage record required?`** is **yes**. **Stage id** column = **usage stage id** (`model_policy.yaml` → `stage_actions` keys; same as `skills/dev-process/templates/model_usage.md`). This is **not** the same as `state.yaml` → `current_stage` (orchestrator stages: `spec`, `plan`, `test`, `implementation`, `final`). For primary-loop **draft** work (spec/plan/test body), omit `--stage-id` and resolve via `current_stage` → `stage_defaults`.

| Stage id | Selected review-depth preset | Main model expectation | Reasoning effort expectation | Token/cost evidence plan | Evidence captured (redacted summaries only) |
|----------|------------------------------|------------------------|-----------------------------|--------------------------|---------------------------------------------|
| `spec_review` | | | | `hermes sessions export` / dashboard / insights | |
| `human_spec_gate` | | | | | |
| `plan_review` | | | | | |
| `test_review` | | | | | |
| `implementation` | | | | | |
| `implementation_review` | | | | | |
| `final_review` | | | | | |
| `final_summary` | | | | | |
| `final_human_gate` | | | | | |

**Deep preset:** checkpoint rows (`implementation_review`, …) follow the **standard** target recipes in `skills/dev-process/review/SKILL.md`; **final** review uses the full reviewer set in `skills/dev-process/review/presets.md`.

## Implementation phases

Size each phase per `skills/dev-process/plan/SKILL.md` § **Implementation phase sizing**. Prefer more **medium** phases over one **heavy** phase. Do not subdivide **light** phases.

| Phase | Objective | Key files (expected) | Size (`light` / `medium` / `heavy`) | Split note |
|-------|-----------|----------------------|---------------------------------------|------------|
| 1 | | | | `—` or why split / waiver |
| 2 | | | | |

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

**Per-phase synthesis (optional skip):** For a **low-risk** implementation phase (`light` size, focused diff, existing tests green, no API/architecture/security scope), you **may** skip per-phase synthesis if the plan documents **Reason** here and records the skip on **`artifacts.timeline`**. Do **not** skip final synthesis when merge/completion decisions matter.

## Test strategy

- Red-test expectation before implementation: [yes / no — justify if no, must align with spec]  
- Focused test paths / markers:  

## Escalation triggers (human)

Cross-check escalation triggers with `skills/dev-process/plan/SKILL.md` (API changes, architecture, scope creep, blocking reviews, etc.).
