# Model / reasoning usage log

**Purpose:** Correlate Hermes/runtime **sessions** with dev-process **stages**, **preset**, and **reasoning**, when analytics alone cannot attribute token/cost to a specific stage.

This file **does not replace** Hermes Dashboard / `hermes insights` token or cost analytics. It **only** maps stages and presets to sessions or summarized evidence so **per-model** analytics can be interpreted **by dev-process stage** when possible.

**Bindings:** **`state.yaml` → `artifacts.model_usage`** (task-root Markdown; numbering rules: `skills/dev-process/artifacts/SKILL.md` § Numbered task-root artifacts). Append **one row per major stage boundary** when model/reasoning choice matters for audit—not every tool call.

If one stage spans **multiple substantive Hermes sessions**, add **one row per session** or **one summary row** listing multiple session ids—do not log every helper or tool call.

**Evidence / privacy:** Do not paste raw logs, full prompts, secrets, credentials, or unrelated user paths into this file. Record **redacted snippets**, session ids, and command names (e.g. `hermes insights --days 7`) only.

| Time | Stage | Preset (current) | Main model (expected/evidence) | Reasoning (expected / observed if available) | Session id | Evidence |
|------|-------|------------------|---------------------------------|---------------------------------------|------------|----------|
| | spec | | | | | logs / `hermes sessions` |
| | plan | | | | | |
| | plan review | | | | | |
| | test | | | | | |
| | implementation | | | | | |
| | final review | | | | | |

**Evidence column:** summarized pointers only — e.g. `hermes insights --days 7`, Dashboard per-model row, **redacted** one-line log hint, `hermes sessions export` path. Logs under `~/.hermes/logs/` may contain sensitive content; excerpt carefully.

If preset or reasoning escalates mid-task, add a row and cite **`artifacts.timeline`**.
