# Model usage

**Purpose:** Stage-attributed session token/cost evidence when the approved plan requires it. Hermes `insights` / Dashboard show per-model totals; this table does not replace that—it attributes usage to dev-process **usage stage ids** and presets on the task.

**Bindings:** `state.yaml` → `artifacts.model_usage` (append-only; numbering: [artifacts/SKILL.md](../artifacts/SKILL.md)).

**Row generation:** [scripts/README.md](../scripts/README.md) — `dp_stage_boundary.py --print-markdown-row` (not `session_usage.py --resolve`).

**Usage stage id** (column `Stage id`): keys from `model_policy.yaml` → `stage_actions` (`spec_review`, `implementation`, …). Passed to `dp_stage_boundary.py --stage-id` / `dp_hermes.py --stage-id`.

**State stage** (`state.yaml` → `current_stage`): orchestrator stages only (`spec`, `plan`, `test`, `implementation`, `final`, …). Resolved via `stage_defaults` when no `--stage-id`. Do **not** put state-stage values in this table unless they are also a `stage_actions` key (e.g. `implementation`).

Row examples below omit **human gates** (`human_spec_gate`, `final_human_gate`) — they use `dp-cheap` / `record_gate` and are usually brief; add rows when the plan requires stage-attributed evidence for gates.

| Time | Stage id | Action | Profile / role | Preset / reasoning | Session | Model | Usage / cost | Evidence |
|------|----------|--------|----------------|-------------------|---------|-------|--------------|----------|
| | `spec_review` | | | | | | | |
| | `plan_review` | | | | | | | |
| | `test_review` | | | | | | | |
| | `implementation` | | | | | | | |
| | `implementation_review` | | | | | | | |
| | `final_review` | | | | | | | |
| | `final_summary` | | | | | | | |
| | `final_human_gate` | | | | | | | |

**Cumulative values:** `hermes sessions export` token counts are cumulative per session; deltas between rows for the same session id give per-boundary usage.

**Preset / reasoning column:** `expected …` is policy-only; actual reasoning comes from the Hermes profile `config.yaml` at launch (see [validation/SKILL.md](../validation/SKILL.md)).
