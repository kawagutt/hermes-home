---
name: dev-process-validation
description: >-
  Cost-aware validation, model/reasoning strength policy, Python/Ruff precedence,
  safe deterministic helper execution, script helper listing, and model usage evidence hints.
  Use when choosing checks for a phase or running helpers.
---

# Validation and helpers (`dev-process`)

### cost-aware validation and model use

Prefer deterministic commands over LLM reasoning for mechanical checks: tests, linting, content searches, file existence, artifact paths, YAML/Markdown syntax, and simple validation that required files exist. Cheap/medium checker agents are appropriate for routine artifact completeness, checklist compliance, naming/doc consistency, and simple log summaries. Reserve higher-cost models for spec/plan reasoning, architecture/impact review, ambiguous failure diagnosis, final synthesis, and blocker triage. Cheap checkers may flag possible blockers, but final blocker decisions must escalate to synthesis or a higher-reasoning reviewer. This is process guidance, not runtime model-routing automation.

### Model strength policy

dev-process **does not** bind concrete provider or model IDs. **Logical roles and Hermes profile *names*** (for example `dp-strong`, `dp-review`, `dp-code`, `dp-cheap`) **are** bound in [`config/model_policy.yaml`](../config/model_policy.yaml); those profiles must exist in your Hermes install (`hermes profile create …`). Actual API models and providers stay in each profile’s Hermes `config.yaml` / `.env` — not in dev-process skills.

Launch profiles with [`scripts/dp_hermes.py`](../scripts/dp_hermes.py) / [`scripts/dp_stage_boundary.py`](../scripts/dp_stage_boundary.py) ([`scripts/README.md`](../scripts/README.md)). Resolution: [`config/model_policy.yaml`](../config/model_policy.yaml) (`stage_actions` = usage `--stage-id`; `stage_defaults` = `state.yaml` → `current_stage`). Profiles apply at **process start** only.

**`reasoning_expected`** is policy-only for `artifacts.model_usage`; actual effort is each profile’s `config.yaml` ([`examples/hermes-profiles.dp.yaml`](../examples/hermes-profiles.dp.yaml)). Before **`final_review`** on **`standard`** / **`deep`**, run [`check_hermes_profiles.py`](../scripts/check_hermes_profiles.py) (or `check_helper_env.py --check-profiles --strict-profiles`) so `dp-strong`/`dp-review`/`dp-code`/`dp-cheap` match expected `agent.reasoning_effort` tiers.

**Review worker sessions:** `dp_review_job.py` + `reviews/.../review_manifest.yaml` only — not `artifacts.model_usage`; no `--record-state` on `review_*` actions.

### Primary session governance

- **`handoff_required=true`:** Hermes profile changes — **MUST** start a new session (`dp_hermes.py --stage-id <usage-stage> --record-state …`).
- **`session_reset_required=true`:** `standard` / `deep` primary boundary — **MUST** start a new session even if the profile is unchanged (one `model_usage` row = one session).
- **`process_violation_if_same_session`** = `handoff_required OR session_reset_required`.
- **`light`:** profile handoff is MUST; other reuse may be documented in timeline/plan (waiver = deviation record, not strict pass on `standard`/`deep` rules).
- **`context_reset_recommended`:** advisory (`light` only).
- Run **`validate_model_governance.py --strict`** before final on **`standard`** / **`deep`**.

Stage-boundary commands, Hermes CLI examples, and governance checks: [scripts/README.md § Stage boundaries](../scripts/README.md#stage-boundaries), [§ validate_model_governance.py](../scripts/README.md#validate_model_governancepy).

### Primary segment boundary completion

**Governance invariant:** A stage is not complete for governance purposes until its required session evidence is recorded.

**Primary invariant:** A primary segment boundary is not complete until the completed segment has a `model_usage` row produced by `dp_stage_boundary.py --print-markdown-row`.

When **`Model usage record required?`** is **yes** (default on **`standard`** / **`deep`**), at each **primary** segment boundary:

1. **Identify** the completed Hermes session id. Use `hermes sessions list` **only when needed**.
2. **Export** it: `hermes sessions export <path>.jsonl --session-id '<id>'`.
3. **Append** a row: `dp_stage_boundary.py --task-dir … --stage-id '<completed-stage>' --dev-action '…' --session-export <path>.jsonl --print-markdown-row` → append to **`artifacts.model_usage`** (do **not** hand-write rows or use `session_usage.py` for dev-process table rows).
4. **Start** the next primary segment: `dp_stage_boundary.py --task-dir … --stage-id '<next>' --print-json`, then `dp_hermes.py --task-dir … --stage-id '<next>' --record-state -- chat` (updates `last_hermes_profile` only after Hermes exits 0).

**Boundary row completion (when `model_usage` is required):**

```text
Primary boundary row must exist.
Session must be a real session id, unless the row explicitly records temporary unknown with a reason.
For standard/deep, temporary unknown must be resolved or documented as a human-known waiver before final review / final gate.
```

- **Reasonless `unknown` or blank `Session` is not acceptable** as a completed boundary.
- **`Session: unknown`** is allowed only as **temporary** observation failure with a **short reason** in the row or adjacent note.
- Before **`final_review`** or **`final_human_gate`** on **`standard`** / **`deep`**: replace with a real session id, or record a **human-known waiver** in **`artifacts.timeline`** / plan **Reason** (e.g. `unknown waiver`, `session lost`, `cannot observe`).
- A waiver is a **human-visible known deviation record**. A waiver can allow a temporary **`Session: unknown`** to pass **`validate_model_governance.py --strict`** (exit 0; may print WARNING) only when the waiver text matches the **stage id** and an accepted governance waiver marker (`unknown waiver`, `session lost`, `cannot observe`, etc.). It does **not** waive missing rows, blank sessions, `review_manifest` session gaps, duplicate sessions, profile/handoff violations, or missing **`last_hermes_profile`** on **`standard`** / **`deep`** when **`model_usage_required`** is true.

Do **not** advance the orchestrator to the **next primary segment** until the completed segment’s boundary row is recorded. When the boundary is represented by **`current_stage`**, do **not** update **`current_stage`** before that row exists (orchestrator: [goal/SKILL.md](../goal/SKILL.md)).

Typical Hermes layout (adjust to team defaults):

| Role | Tier | Reasoning effort |
|------|------|------------------|
| Primary dev-process loop (spec / plan / tests / implementation / reviews) | Strongest configured **main model** (e.g. team default for coding agents) | Tied to **review-depth preset** — see § **Reasoning effort by review-depth preset** |
| Deterministic helpers | No LLM | — |
| Side tasks (auxiliary tier: approval, title, compression, session search, web extract, vision) | Cheapest **Codex-compatible** auxiliary tier acceptable for shallow work | none / lowest available |

Higher reasoning effort is not automatically better—it is slower, costlier, and can overthink ([OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning)). **Preset** selects depth; reasoning effort follows the table below—not every stage at maximum.

Preset selection rules: [review/presets.md](../review/presets.md).

### Reasoning effort by review-depth preset

When the **runtime** supports reasoning-effort selection (e.g. Hermes `/reasoning`), tie effort to the **selected review-depth preset** for the task. Do **not** use **high** on `light` by default—**escalate the preset** to `deep` instead of secretly cranking reasoning. Preset aliases (`fast`, `high-risk`) are defined only in [review/presets.md](../review/presets.md).

| Preset | Typical main model policy | Reasoning effort policy |
|--------|---------------------------|-------------------------|
| `light` | **main model** | **Do not** use **high**. Use deterministic helpers first; **default/medium** reasoning effort (or runtime default) only. If risk rises, escalate **preset** to `standard` or `deep`. |
| `standard` | **main model** | **default/medium** reasoning effort for spec, plan, implementation, and routine reviews. **Escalate to `deep` before adopting high reasoning**, except when a human explicitly requests high for a **narrow** decision. |
| `deep` | **main model** | **high** reasoning effort for synthesis, blocker/rework-owner triage when ambiguous, architecture/impact judgment where consequences are unclear, human-gate prep with **required human decisions**, and **final completion / merge recommendation** when unresolved risk remains. |

**`deep` is not “everything high”:** per [`model_policy.yaml`](../config/model_policy.yaml) → `reasoning_by_preset.deep`, **checkpoint reviews** (`implementation_review`, routine `review_main` work) stay at **medium** reasoning expectation; **final synthesis**, **`final_review`**, ambiguous blocker triage, and merge recommendations use **high**. Match Hermes profile `config.yaml` to that split (`dp-review` for checkpoint, `dp-strong` for final/deep synthesis).

**Use high reasoning when** (aligned with **`deep`** triggers in [review/presets.md](../review/presets.md)):

- active preset is `deep`, or preset was just escalated to `deep`; or  
- public **API** / **CLI** / **user-visible behavior** changes; **architecture / boundary** changes; **migration / schema / persistence**; **security / permission / privacy**;  
- blocker triage or rework-owner assignment is **ambiguous**; **reviewer disagreement** remains; final completion decision has **unresolved risk**.

**`standard` mid-task:** Stay on **medium** for local/non-blocking work. Escalate to **`deep` + high** when: blocker ambiguity appears, architecture/API risk surfaces, review exposes high-risk triggers, or disagreement persists.

**Do not use high reasoning under `light` for**:

- artifact existence / numbered-file conventions;  
- **grep**, **find**, **ls**; Markdown/YAML sanity;  
- **`review_round.py`**, **`validate_state.py`**; trivial naming/doc lint;  
- docs-only edits with clear deterministic validation equivalent.

Spend **high** reasoning on **remaining uncertainty and high impact**, not on mechanical validation.

### Model usage

Hermes can show **per-model tokens and estimated cost** (Hermes Dashboard Analytics, Models page); CLI: `hermes insights`. That does **not** attribute usage to dev-process **stages** or **preset**—record that on the task.

**When to create `artifacts.model_usage`:** **Default yes** for preset **`standard`** or **`deep`**—materialize and append rows at major stage boundaries. Preset **`light`** or trivial docs-only / mechanical tasks **may** set **`Model usage record required?`** to **no** with reason `no need` (see [templates/plan.md](../templates/plan.md)) and leave **`artifacts.model_usage`** empty. Skipping on **`standard`**/**`deep`** requires **explicit human approval** in **`artifacts.plan` Reason**. Recording cost is negligible when enabled.

**Evidence preference order** (cheap and low-risk first):

1. **`hermes insights`** / Hermes Dashboard **per-model** summary  
2. **`hermes sessions list`** / **`hermes sessions stats`**  
3. **`hermes sessions export`** … with redaction as needed  
4. **Redacted grep** of `~/.hermes/logs` **only** when the above is insufficient  

**If `Model usage record required?` is yes** but model or reasoning **cannot** be observed: record **`unknown`** with a **short reason** (gateway did not expose setting, session lost, etc.) in **`artifacts.model_usage`** and/or **`artifacts.final_summary_ja`**—do **not** leave the field silently blank. Treat this as **temporary**; before **`final_review`** / **`final_human_gate`** on **`standard`** / **`deep`**, resolve to a real session id or document a human-known waiver (see § Primary segment boundary completion).

**Materialize once:** copy [templates/model_usage.md](../templates/model_usage.md) to the task root with correct `NNNN_` numbering; set `state.yaml` → **`artifacts.model_usage`** in the **same session**. **Append rows** at major boundaries; see template for multi-session rules ([artifacts/SKILL.md](../artifacts/SKILL.md) — append-only `model_usage` under **append-only task artifacts**).

The plan always includes the **compact** model usage block (`Model usage record required?`, `Reason`, `Artifact`); expand the **optional per-stage** table in the plan only when **`Model usage record required?`** is **yes**.

**Recording:** default **yes** on `standard`/`deep`; one boundary → one row ([`templates/model_usage.md`](../templates/model_usage.md)). Procedure and Hermes CLI: [scripts/README.md § Stage boundaries](../scripts/README.md#stage-boundaries). Do **not** paste raw logs into artifacts — redacted session id / model / command only.

**Governance (`--strict`):** required rows from [`config/primary_segments.yaml`](../config/primary_segments.yaml) (`spec`, `plan`, `test`, `implementation` or `implementation_phase_NN`, `final_*`). Review/checkpoint sessions → `review_manifest.yaml` only. Details: [scripts/README.md § validate_model_governance.py](../scripts/README.md#validate_model_governancepy).

For Python validation on Python changes, precedence is: user-explicit command > project docs/config (`AGENTS.md`, README, Makefile, `pyproject.toml`, etc.) > dev-process default. If no project rule exists, plan Ruff checks per Python-changing phase, preferably `uv run ruff check <touched-python-paths>` or `.venv/bin/python -m ruff check <touched-python-paths>` when appropriate. Do not silently use unrelated system Python when the project appears to use `uv` / `.venv`; stop and report environment ambiguity.

### Safe deterministic helper execution

When already covered by the approved plan or dev-process helper policy, safe deterministic commands may run **without asking the human each time**.

Examples:

- `validate_state.py`
- `validate_model_governance.py` (default; `--strict` before final on standard/deep)
- `check_helper_env.py` (optional `--check-profiles --strict-profiles` when Hermes profiles are installed)
- `check_hermes_profiles.py` (or via `check_helper_env --check-profiles`)
- `review_round.py --dry-run`
- `review_round.py --create` only for the **current approved review stage** (stage and next round already implied by the approved plan or the active review step; do not spin arbitrary extra rounds)
- `hermes sessions list` / `hermes sessions export` for stage-boundary usage recording
- `dp_stage_boundary.py` / `dp_hermes.py` for per-stage Hermes profile resolution, handoff, and **`artifacts.model_usage`** row append (`--print-markdown-row`)
- `session_usage.py` — parse `hermes sessions export` JSONL only (used by `dp_stage_boundary`; do **not** append dev-process table rows with `session_usage.py` alone)
- `grep` / `find` / `ls` checks
- Markdown / YAML validation
- targeted lint/test commands listed in `phase_checklists`

Still stop or ask before commands that:

- modify product files unexpectedly;
- switch/create branches unless at the task branch precondition step;
- commit, merge, push, or delete files;
- access secrets;
- use network or external services unexpectedly;
- are outside the approved plan.

### Deterministic helper utilities

Small deterministic helpers live under [`scripts/`](../scripts/) and are documented in [`scripts/README.md`](../scripts/README.md). They reduce mechanical process mistakes but are **not** a workflow engine and do not replace role judgment, reviewer synthesis, human gates, or approved plans.

Current helpers:

- `validate_state.py` — task state/artifact/review/branch consistency checks; **human gate consistency** on `pending_human_gate` vs `reviewed.*` / `approved.*` (see [`scripts/README.md`](../scripts/README.md)); **governance preflight** (ERROR on missing `last_hermes_profile` only near final review/gate on `standard`/`deep` with `model_usage_required`—not on `current_stage: final` alone); always warns on missing `last_hermes_profile` elsewhere; warns on `current_stage` clearly past a gate wait; errors when `current_stage` is a usage-only `stage_actions` id (e.g. `spec_review`). Pass the task directory (`.hermes/tasks/<task-id>`), not the `state.yaml` file path. Use `--strict` to fail on warnings. When a human rejects a gate or requests rework, the orchestrator must clear `pending_human_gate` and reset the matching `reviewed.*` marker to `false` before routing rework.
- `validate_model_governance.py` — primary `model_usage` session evidence + latest `review_manifest.yaml` checks; `--strict` before final on standard/deep.
- `check_helper_env.py` — PyYAML + bundled policy + helper `--help` preflight; optional `--check-profiles`.
- `check_hermes_profiles.py` — `agent.reasoning_effort` in `~/.hermes/profiles/*/config.yaml` vs [`config/hermes_profile_expectations.yaml`](../config/hermes_profile_expectations.yaml).
- `dp_hermes.py` — supports `--handoff-only` (resolve JSON only, no Hermes launch) when inspecting profile handoffs.
- `review_round.py` — create a review round directory, then finish it only after real synthesis exists.
- `branch_precondition.py` — verify/record task branch precondition evidence and append a timeline row.
- `dp_stage_boundary.py` — stage-boundary resolve + optional `artifacts.model_usage` Markdown row.
- `session_usage.py` — parse `hermes sessions export` JSONL only (JSON or manual Markdown row).

NodeFlow integration is out of scope for dev-process v3 unless a future approved task explicitly adds it.

### Review-depth preset selection

Review depth is selected by **remaining uncertainty** and **impact if broken**, not by diff size alone. First run deterministic checks where possible, then choose the smallest preset that still covers the remaining risk. Human preference for a lighter preset does not override high-risk triggers.

Canonical preset definitions live in [`review/presets.md`](../review/presets.md). Do not define competing reviewer lists or synthesis rules elsewhere.
