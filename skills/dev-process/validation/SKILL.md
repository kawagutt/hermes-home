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

To start Hermes with the correct profile for a dev-process **action** or **stage** without editing global config, use [`scripts/dp_hermes.py`](../scripts/dp_hermes.py) or [`scripts/dp_stage_boundary.py`](../scripts/dp_stage_boundary.py) (see [scripts/README.md](../scripts/README.md)). Resolution uses [`config/model_policy.yaml`](../config/model_policy.yaml) (`schema_version: 2`): **`stage_actions`** maps **usage stage ids** (`--stage-id`, `artifacts.model_usage` rows) to actions/profiles; **`stage_defaults`** maps **state stages** (`state.yaml` → `current_stage`). `reasoning_by_preset` ties effort to **`state.yaml` → `review_depth_preset`**. The wrapper only applies the profile at **process start**—**start a new Hermes session** when `handoff_required` is true; it does not switch models mid-session.

**Per-task automatic switching (required at stage boundaries):** Before each major stage in `/goal`, run `dp_stage_boundary.py --task-dir … --stage-id <next-stage> --print-json`, then launch with `dp_hermes.py --record-state …` (or `hermes --profile=…`). Configure distinct models per profile under `~/.hermes/profiles/` (see [examples/hermes-profiles.dp.yaml](../examples/hermes-profiles.dp.yaml)).

**`reasoning_expected` is not runtime control:** Values from `reasoning_by_preset` in `model_policy.yaml` are **policy expectations for `artifacts.model_usage` only**. `dp_hermes.py` sets **`--profile=<name>` only**; it does **not** change Hermes `agent.reasoning_effort`. Actual effort comes from the launched profile’s `config.yaml` (e.g. set `dp-strong` → `high`, `dp-cheap` → `low` per [examples/hermes-profiles.dp.yaml](../examples/hermes-profiles.dp.yaml)).

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

**When to create `artifacts.model_usage`:** **Default yes** for preset **`standard`** or **`deep`**—materialize and append rows at major stage boundaries. Preset **`light`** or trivial docs-only / mechanical tasks **may** set **`Model usage record required?`** to **no** with reason `no need` (see [templates/plan.md](../templates/plan.md)). Skipping on **`standard`**/**`deep`** requires **explicit human approval** in **`artifacts.plan` Reason**. Recording cost is negligible when enabled.

**Evidence preference order** (cheap and low-risk first):

1. **`hermes insights`** / Hermes Dashboard **per-model** summary  
2. **`hermes sessions list`** / **`hermes sessions stats`**  
3. **`hermes sessions export`** … with redaction as needed  
4. **Redacted grep** of `~/.hermes/logs` **only** when the above is insufficient  

**If `Model usage record required?` is yes** but model or reasoning **cannot** be observed: record **`unknown`** and a **short reason** (gateway did not expose setting, session lost, etc.) in **`artifacts.model_usage`** and/or **`artifacts.final_summary_ja`**—do **not** leave the field silently blank.

**Materialize once:** copy [templates/model_usage.md](../templates/model_usage.md) to the task root with correct `NNNN_` numbering; set `state.yaml` → **`artifacts.model_usage`** in the **same session**. **Append rows** at major boundaries; see template for multi-session rules ([artifacts/SKILL.md](../artifacts/SKILL.md) — append-only `model_usage` under **append-only task artifacts**).

The plan always includes the **compact** model usage block (`Model usage record required?`, `Reason`, `Artifact`); expand the **optional per-stage** table in the plan only when **`Model usage record required?`** is **yes**.

### Default stage-boundary usage recording

When **`Model usage record required?`** is **yes** (default for **`standard`** / **`deep`**; **`light`** may omit per [templates/plan.md](../templates/plan.md)), append one row per major boundary to **`artifacts.model_usage`**.

**Procedure:** [scripts/README.md § Stage boundaries](../scripts/README.md#stage-boundaries) (`hermes sessions export` + `dp_stage_boundary.py --print-markdown-row`). Use `--stage-id` for the **completed** stage. Cumulative token semantics: [templates/model_usage.md](../templates/model_usage.md).

**Useful Hermes-facing commands** (availability depends on install; see [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)):

```bash
hermes insights --days 7
hermes insights --days 30
hermes dashboard
hermes sessions list
hermes sessions stats
hermes sessions export /tmp/hermes_sessions.jsonl --session-id '<session-id>'
hermes logs list
hermes logs -n 200
hermes logs --level INFO --since 2h
hermes logs --session '<session-id>'
```

Grepping local logs (last resort; see **Evidence preference order** above):

```bash
grep -RniE 'gpt-5\.|model|provider|token|usage|cost|reasoning|auxiliary' ~/.hermes/logs | tail -n 200
```

Do **not** paste raw log output into task-root artifacts when it may include **secrets**, **private prompt content**, **tokens**, **credentials**, **full file paths**, or **unrelated user data**. Keep **redacted snippets** or summarized evidence (session id, model name, CLI command used) in **`artifacts.model_usage`** and **`artifacts.final_summary_ja`**.

**Record at each boundary:**

- task id (`state.yaml`)
- stage (spec, plan review, …)
- preset effective for that slice
- reasoning expected by plan vs **observed** session setting if available
- session id(s) for Hermes sessions in the primary dev-process loop
- session token usage (`input_tokens`, `output_tokens`, `reasoning_tokens`; note cache tokens separately if relevant)
- session cost evidence (`actual_cost_usd` and/or `estimated_cost_usd` when available)
- pointer to insights/Dashboard/export or redacted log line
- whether the token values are cumulative within a shared session (note in Evidence if so)

For consistent extraction from exported session JSONL, use:

```bash
python3 skills/dev-process/scripts/session_usage.py /tmp/hermes_session.jsonl --format json
```

or generate a complete row:

```bash
python3 skills/dev-process/scripts/session_usage.py /tmp/hermes_session.jsonl \
  --format markdown --time auto --stage-id test --preset deep --reasoning 'high / observed medium'
```

For Python validation on Python changes, precedence is: user-explicit command > project docs/config (`AGENTS.md`, README, Makefile, `pyproject.toml`, etc.) > dev-process default. If no project rule exists, plan Ruff checks per Python-changing phase, preferably `uv run ruff check <touched-python-paths>` or `.venv/bin/python -m ruff check <touched-python-paths>` when appropriate. Do not silently use unrelated system Python when the project appears to use `uv` / `.venv`; stop and report environment ambiguity.

### Safe deterministic helper execution

When already covered by the approved plan or dev-process helper policy, safe deterministic commands may run **without asking the human each time**.

Examples:

- `validate_state.py`
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

- `validate_state.py` — task state/artifact/review/branch consistency checks. Pass the task directory (`.hermes/tasks/<task-id>`), not the `state.yaml` file path.
- `review_round.py` — create a review round directory, then finish it only after real synthesis exists.
- `branch_precondition.py` — verify/record task branch precondition evidence and append a timeline row.
- `dp_hermes.py` — resolve Hermes profile from `model_policy.yaml` + task state; optionally launch `hermes --profile=…`.
- `dp_stage_boundary.py` — stage-boundary resolve + optional `artifacts.model_usage` Markdown row.
- `session_usage.py` — parse `hermes sessions export` JSONL only (JSON or manual Markdown row).

NodeFlow integration is out of scope for dev-process v3 unless a future approved task explicitly adds it.

### Review-depth preset selection

Review depth is selected by **remaining uncertainty** and **impact if broken**, not by diff size alone. First run deterministic checks where possible, then choose the smallest preset that still covers the remaining risk. Human preference for a lighter preset does not override high-risk triggers.

Canonical preset definitions live in [`review/presets.md`](../review/presets.md). Do not define competing reviewer lists or synthesis rules elsewhere.
