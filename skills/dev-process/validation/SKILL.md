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

**If `Model usage record required?` is yes** but model or reasoning **cannot** be observed: record **`unknown`** and a **short reason** (gateway did not expose setting, session lost, etc.) in **`artifacts.model_usage`** and/or **`artifacts.final_summary_ja`**—do **not** leave the field silently blank.

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
- `dp_stage_boundary.py` / `dp_hermes.py` for per-stage Hermes profile resolution and handoff
- `session_usage.py` to generate `artifacts.model_usage` rows from exported session JSONL
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

- `validate_state.py` — task state/artifact/review/branch consistency checks; **human gate consistency** on `pending_human_gate` vs `reviewed.*` / `approved.*` (see [`scripts/README.md`](../scripts/README.md)); warns on missing `last_hermes_profile` and on `current_stage` clearly past a gate wait; errors when `current_stage` is a usage-only `stage_actions` id (e.g. `spec_review`). Pass the task directory (`.hermes/tasks/<task-id>`), not the `state.yaml` file path. Use `--strict` to fail on warnings. When a human rejects a gate or requests rework, the orchestrator must clear `pending_human_gate` and reset the matching `reviewed.*` marker to `false` before routing rework.
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
