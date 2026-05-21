# Model usage

**Purpose:** Stage-attributed session token/cost evidence when the approved plan requires it. Hermes `insights` / Dashboard show per-model totals; this table does not replace that—it attributes usage to dev-process **primary segment** stage ids and presets on the task.

**Bindings:** `state.yaml` → `artifacts.model_usage` (append-only; numbering: [artifacts/SKILL.md](../artifacts/SKILL.md)).

**Row generation:** [scripts/README.md](../scripts/README.md) — `dp_stage_boundary.py --print-markdown-row` (not `session_usage.py --resolve`).

**Usage stage id** (column `Stage id`): primary-loop segments (`spec`, `plan`, `test`, `implementation` or `implementation_phase_NN`, `final_review`, `final_summary`) and other ids resolvable by `dp_stage_boundary.py` / `dp_hermes.py --stage-id`. Review worker sessions use `review_manifest.yaml` only — do not duplicate them here.

**State stage** (`state.yaml` → `current_stage`): orchestrator stages only (`spec`, `plan`, `test`, `implementation`, `final`, …). Resolved via `stage_defaults` when no `--stage-id`. The `Stage id` column may use the same name for primary draft segments (`spec`, `plan`, `test`) even though review rounds use `reviews/<stage>/`.

**Column contract (validator):** Header names are fixed. **`Session`** holds the Hermes **session id only** (backticks or plain `YYYYMMDD_HHMMSS_abcdef`).

**Primary segment session rule (`standard` / `deep`):** One required primary usage row = **one Hermes session**. Do not reuse the same `session_id` across multiple Stage id rows. Cumulative export values are per-session; do not share one session across boundaries unless preset is `light` and a deviation waiver is recorded in timeline/plan (waiver does not make `--strict` pass on `standard`/`deep`).

**`Profile / role` format (fixed):** Leading token is the Hermes profile name; validator reads `dp-*` before `/`:

```text
dp-strong / strong_reasoning
dp-review / review_main
dp-code / code_main
dp-cheap / cheap_aux
```

`dp_stage_boundary.py --print-markdown-row` emits this shape.

| Time | Stage id | Action | Profile / role | Preset / reasoning | Session | Model | Usage / cost | Evidence |
|------|----------|--------|----------------|-------------------|---------|-------|--------------|----------|
| | `spec` | | | | | | | |
| | `plan` | | | | | | | |
| | `test` | | | | | | | |
| | `implementation` | | | | | | | |
| | `implementation_phase_01` | | | | | | | |
| | `final_review` | | | | | | | |
| | `final_summary` | | | | | | | |

Row examples omit **human gates** (`human_spec_gate`, `final_human_gate`) unless the plan requires stage-attributed evidence. Optional boundary ids such as `spec_review` belong in the plan optional table when used; review worker sessions still go in `review_manifest.yaml`.

**Token values:** `hermes sessions export` reports cumulative tokens per session. Each row should use a **distinct** session id for its boundary; do not rely on deltas from a shared session id on `standard`/`deep` tasks.

**Preset / reasoning column:** `expected …` is policy-only; actual reasoning comes from the Hermes profile `config.yaml` at launch (see [validation/SKILL.md](../validation/SKILL.md)).

## Segment boundary completion

Canonical procedure: [validation/SKILL.md § Primary segment boundary completion](../validation/SKILL.md#primary-segment-boundary-completion).

**Invariant:** A primary segment boundary is not complete until the completed segment has a row here produced by `dp_stage_boundary.py --print-markdown-row` (not a hand-written or `session_usage.py`-only row).

1. Identify the completed Hermes session id (`hermes sessions list` only when needed).
2. `hermes sessions export … --session-id '<id>'`
3. `dp_stage_boundary.py … --print-markdown-row` → append to this file
4. Next segment: `dp_stage_boundary.py --task-dir … --stage-id '<next>' --print-json`, then `dp_hermes.py --task-dir … --stage-id '<next>' --record-state -- chat`

**`Session` column:** Prefer a real session id. Temporary **`unknown`** is allowed only with an explicit reason in the row; before **`final_review`** / **`final_human_gate`** on **`standard`** / **`deep`**, resolve to a real id or record a human-known waiver in **`artifacts.timeline`** / plan **Reason**. A waiver can allow a temporary unknown Session to pass **`validate_model_governance.py --strict`** only when it matches the stage id and an accepted governance waiver marker. It does not waive missing rows, blank sessions, review_manifest session gaps, duplicate sessions, profile/handoff violations, or missing last_hermes_profile.

**Review workers:** Record sessions in `reviews/<stage>/round_NN/review_manifest.yaml` only—do not duplicate reviewer or synthesis sessions in this table.
