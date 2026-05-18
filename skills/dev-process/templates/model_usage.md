# Model usage

**Purpose:** Stage-attributed session token/cost evidence when the approved plan requires it.

**Bindings:** `state.yaml` → `artifacts.model_usage` (append-only; numbering: [artifacts/SKILL.md](../artifacts/SKILL.md)).

**Row generation:** [scripts/README.md](../scripts/README.md) — `dp_stage_boundary.py --print-markdown-row` (not `session_usage.py --resolve`).

**Stage ids:** `stage_actions` keys in [config/model_policy.yaml](../config/model_policy.yaml) (`spec_review`, `plan_review`, …). `state.yaml` → `current_stage` uses canonical stages only (`spec`, `plan`, `implementation`, …).

| Time | Stage id | Action | Profile / role | Preset / reasoning | Session | Model | Usage / cost | Evidence |
|------|----------|--------|----------------|-------------------|---------|-------|--------------|----------|
| | `spec_review` | | | | | | | |
| | `plan_review` | | | | | | | |
| | `test_review` | | | | | | | |
| | `implementation_review` | | | | | | | |
| | `final_review` | | | | | | | |
| | `final_human_gate` | | | | | | | |

**Cumulative values:** `hermes sessions export` token counts are cumulative per session; deltas between rows for the same session id give per-boundary usage.

**Preset / reasoning column:** `expected …` is policy-only; actual reasoning comes from the Hermes profile `config.yaml` at launch (see [validation/SKILL.md](../validation/SKILL.md)).
