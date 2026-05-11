# Model usage

**Purpose:** Correlate Hermes/runtime **sessions** with dev-process **stages**, **review-depth preset**, and **reasoning effort**, when Hermes Dashboard / analytics alone cannot attribute token/cost to a specific stage.

This file **does not replace** Hermes Dashboard / `hermes insights` token or cost analytics. It **only** maps stages and presets to sessions or summarized evidence so **per-model** analytics can be interpreted **by dev-process stage** when possible.

**Bindings:** **`state.yaml` → `artifacts.model_usage`** (task-root Markdown; numbering rules: `skills/dev-process/artifacts/SKILL.md` § Numbered task-root artifacts). Append **one row per major stage boundary** when model choice or **reasoning effort** matters for cost or accountability—not every tool call.

If one stage spans **multiple Hermes sessions** in the primary dev-process loop, add **one row per session** or **one summary row** listing multiple session ids—do not log every helper or tool call.

**Evidence / privacy:** Do not paste raw logs, full prompts, secrets, credentials, or unrelated user paths into this file. Record **redacted snippets**, session ids, and command names (e.g. `hermes insights --days 7`) only.

**Stage ids** use the same labels as **`artifacts.plan`** (Model usage § optional per-stage table): they mirror **`state.yaml`** (`current_stage`, `review_rounds` keys), **`reviews/<stage>/`** (`spec`, `plan`, `test`, `final`, …), the spec gate (**`human_spec_gate`** / **`artifacts.human_spec_gate`**), implementation checkpoint reviews (**`implementation_review`** ↔ `reviews/implementation_phase_*/`), and end-of-task artifacts (**`final_summary`**, **`final_human_gate`**).

When using Hermes with dev-process profile resolution, optionally note **`dp_hermes.py` --action**, the logical **role** from [`skills/dev-process/config/model_policy.yaml`](../config/model_policy.yaml), and the **Hermes profile** name (not the raw API model id).

| Time | Stage id | dev-process action (if any) | Logical role | Hermes profile | Selected review-depth preset | Main model (expected/evidence) | Reasoning effort (expected / observed if available) | Session id | Evidence |
|------|----------|-------------------------------|--------------|----------------|------------------------------|--------------------------------|-----------------------------------------------------|------------|----------|
| | `spec` | | | | | | | | logs / `hermes sessions` |
| | `spec_review` | | | | | | | | |
| | `human_spec_gate` | | | | | | | | |
| | `plan` | | | | | | | | |
| | `plan_review` | | | | | | | | |
| | `test` | | | | | | | | |
| | `test_review` | | | | | | | | |
| | `implementation` | | | | | | | | |
| | `implementation_review` | | | | | | | | |
| | `final_review` | | | | | | | | |
| | `final_summary` | | | | | | | | |
| | `final_human_gate` | | | | | | | | |

**Evidence column:** summarized pointers only — e.g. `hermes insights --days 7`, Hermes Dashboard per-model row, **redacted** one-line log hint, `hermes sessions export` path. Logs under `~/.hermes/logs/` may contain sensitive content; excerpt carefully.

If preset or reasoning effort escalates mid-task, add a row and cite **`artifacts.timeline`**.
