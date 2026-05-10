---
name: dev-process-validation
description: >-
  Cost-aware validation, Python/Ruff precedence, safe deterministic helper execution, and
  script helper listing for dev-process. Use when choosing checks for a phase or running helpers.
---

# Validation and helpers (`dev-process`)

### cost-aware validation and model use

Prefer deterministic commands over LLM reasoning for mechanical checks: tests, linting, content searches, file existence, artifact paths, YAML/Markdown syntax, and simple validation that required files exist. Cheap/medium checker agents are appropriate for routine artifact completeness, checklist compliance, naming/doc consistency, and simple log summaries. Reserve higher-cost models for spec/plan reasoning, architecture/impact review, ambiguous failure diagnosis, final synthesis, and blocker triage. Cheap checkers may flag possible blockers, but final blocker decisions must escalate to synthesis or a higher-reasoning reviewer. This is process guidance, not runtime model-routing automation.

For Python validation on Python changes, precedence is: user-explicit command > project docs/config (`AGENTS.md`, README, Makefile, `pyproject.toml`, etc.) > dev-process default. If no project rule exists, plan Ruff checks per Python-changing phase, preferably `uv run ruff check <touched-python-paths>` or `.venv/bin/python -m ruff check <touched-python-paths>` when appropriate. Do not silently use unrelated system Python when the project appears to use `uv` / `.venv`; stop and report environment ambiguity.

### Safe deterministic helper execution

When already covered by the approved plan or dev-process helper policy, safe deterministic commands may run **without asking the human each time**.

Examples:

- `validate_state.py`
- `review_round.py --dry-run`
- `review_round.py --create` only for the **current approved review stage** (stage and next round already implied by the approved plan or the active review step; do not spin arbitrary extra rounds)
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

- `validate_state.py` — task state/artifact/review/branch consistency checks.
- `review_round.py` — create a review round directory, then finish it only after real synthesis exists.
- `branch_precondition.py` — verify/record task branch precondition evidence and append a timeline row.

NodeFlow integration is out of scope for dev-process v3 unless a future approved task explicitly adds it.

### Review-depth preset selection

Review depth is selected by **remaining uncertainty** and **impact if broken**, not by diff size alone. First run deterministic checks where possible, then choose the smallest preset that still covers the remaining risk. Human preference for a lighter preset does not override high-risk triggers.

Canonical preset definitions live in [`review/presets.md`](../review/presets.md). Do not define competing reviewer lists or synthesis rules elsewhere.
