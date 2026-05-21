---
name: dev-process-validation
description: >-
  v4 Job Contract (J1–J7), run-dp helpers, cost-aware validation, model policy,
  and safe deterministic helper execution. Use when starting/closing jobs or validating tasks.
---

# Validation and helpers (`dev-process`)

## v4 Job Contract (canonical — new tasks only)

**One sentence:** Each new role work starts in a **new Hermes session** as a **job**; on finish, **close** records evidence in `jobs.yaml` and a **handoff** briefs the next job.

| # | Rule | Summary |
|---|------|---------|
| J1 | OneSessionOneJob | 1 session = 1 job |
| J2 | OneJobOneRole | 1 job = 1 role (no mixing) |
| J3 | AlwaysNewSession | Continuation, rework, re-review → new session |
| J4 | HandoffOnlyContext | Do not rely on prior chat. **`handoff_in` is the only cross-session briefing entry.** Authoritative content: spec/plan/reviews/state/repo |
| J5 | HelperOnlyEvidence | `jobs.yaml` via helpers only. Helper **reserves** `handoff_out` paths; the **job agent writes** handoff content. `expected_profile` / `observed_profile` (from export) must match when observable. |
| J6 | CloseBeforeNext | `job close` exit 0 before next `job start` |
| J7 | StrictBeforeFinalGate | `run-dp validate --strict` exit 0 before numbered **final** approval. **No waiver.** |

**Scope:** v4 applies only to **new** tasks with `jobs.yaml`. Completed or pre-v4 tasks are historical — do not repair them to satisfy v4.

**Roles (fixed):** `spec` | `plan` | `test` | `implementation` | `review_worker` | `review_synthesis` | `final_review` | `final_summary`

| role | Hermes profile |
|------|----------------|
| spec, plan, review_synthesis, final_review, final_summary | `dp-strong` |
| test, implementation, review_worker | `dp-code` |

`review_worker` also records `reviewer`, `review_target`, `review_round` on the job.

**Preset** changes review depth only; J1–J7 apply to all presets.

### Public API (`run-dp`)

```bash
run-dp task start --task-dir .hermes/tasks/<task-id>
run-dp job start --task-dir ... --role <role> [--handoff-in PATH ...] [--reviewer ... --review-target ... --review-round N]
run-dp job close --task-dir ... --session-export <path.jsonl> [--session-id <id>] [--artifacts-out key=path ...]
run-dp render model-usage --task-dir ...
run-dp render review-summary --task-dir ...
run-dp validate --task-dir ... [--strict]
```

Use the dp venv when available: `/data/github/hermes-home/.venv-dp/bin/python` or `skills/dev-process/scripts/run-dp`.

**Bounded `/goal`:** `1 /goal = 1 job` then STOP. Deep review: one `/goal` per reviewer job.

### Data model

| File | Role |
|------|------|
| `jobs.yaml` | **SOT** for session / model / job evidence |
| `handoffs/*.md` | Cross-session briefing (navigation layer) |
| `state.yaml` | Orchestration only (`current_stage`, `current_job`, gates, `reviewed.*`, `artifacts.*`) |
| `generated/model_usage.md`, `generated/review_summary.md` | **Generated** display artifacts (`run-dp render`; not numbered task-root artifacts) |

v4 **does not** use: `review_manifest.yaml`, `Session: unknown`, governance waivers, `last_hermes_profile` on new tasks.

### Job lifecycle

1. `run-dp task start` — `check_helper_env.py` first, then `jobs.yaml`, `state.yaml`, `handoffs/`, `generated/`.
2. `run-dp job start --role …` — opens job, probes `hermes --profile=<expected> version`, prints `hermes_launch` (does not start interactive chat). **No session id yet.**
3. Run `hermes_launch` in a **new** session; work only there (J4: read `handoff_in` list + artifacts).
4. Agent writes substantive briefing to `handoff_out` (required sections; not empty).
5. `hermes sessions export …` → `run-dp job close --session-export …` — attaches `session_id` and usage to the job.
6. `run-dp render` refreshes `model_usage.md` / `review_summary.md`.
7. Before **final_human_gate** numbered approval: `run-dp validate --strict` must exit 0 (J7).

**handoff_in:** YAML list (even for one file). Required for every role except `spec`. For `review_synthesis`, list all reviewer `handoff_out` paths plus the review target handoff.

**handoff_out:** Path reserved at `job start`; agent fills before `job close`. Close validates non-empty content. No auto-generated stubs.

### Pre-v4 validation

If `jobs.yaml` is missing:

```text
This task has no jobs.yaml and appears to be pre-v4.
v4 validation is not applicable.
```

`run-dp validate` on pre-v4 tasks prints *not applicable* and exits 0. Use legacy `validate_model_governance.py --strict` for pre-v4 tasks. Do not run `run-dp validate --strict` expecting v4 job rules on old tasks.

### Legacy scripts (pre-v4 / internal)

`dp_stage_boundary.py`, `dp_review_job.py`, `validate_model_governance.py` remain for old tasks. **Do not** use them on new v4 tasks.

---

### cost-aware validation and model use

Prefer deterministic commands over LLM reasoning for mechanical checks: tests, linting, content searches, file existence, artifact paths, YAML/Markdown syntax, and simple validation that required files exist. Cheap/medium checker agents are appropriate for routine artifact completeness, checklist compliance, naming/doc consistency, and simple log summaries. Reserve higher-cost models for spec/plan reasoning, architecture/impact review, ambiguous failure diagnosis, final synthesis, and blocker triage.

### Minimal rules (orchestration)

| Term | Meaning |
| --- | --- |
| **evidence** | Machine-checkable trace (`jobs.yaml`, rendered artifacts, gate artifacts) |
| **record** | Persist in `state.yaml` / task artifacts / `jobs.yaml` (helpers only) |
| **strict** | `run-dp validate --strict` before final gate (v4) |

**State rules:** `reviewed.*` = agent review passed (Proceed). `pending_human_gate` = human gate wait. `approved.*` = human gate approved.

**Gate rules:** If `pending_human_gate` is non-empty, stop. Reject/rework clears `pending_human_gate` and resets matching `reviewed.*` to `false`.

**Validation (v4 tasks):**

| Command | Role |
| --- | --- |
| `run-dp validate` | v4 job contract + `validate_state.py` |
| `run-dp validate --strict` | J6/J7 + state consistency before final gate |
| `validate_state.py` | Gate/review/artifact consistency (all tasks) |

Details: [`scripts/README.md`](../scripts/README.md). Gate invariants: [../SKILL.md § Human gates](../SKILL.md#human-gates).

### Model strength policy

Logical roles → Hermes profile names in [`config/model_policy.yaml`](../config/model_policy.yaml). v4 maps **job roles** to profiles (table above). Launch: `hermes --profile=<profile>` after `run-dp job start` prints resolution JSON.

Preset selection: [review/presets.md](../review/presets.md).

### Safe deterministic helper execution

v4 task helpers (no per-command human ask when plan-approved):

- `run-dp task|job|render|validate`
- `hermes sessions export` for `job close`
- `grep` / `find` / lint / tests per plan

**Pre-v4 only (do not use on new v4 tasks):** `dp_stage_boundary.py`, `dp_review_job.py`, `review_round.py`, `validate_model_governance.py`, `dp_hermes.py --record-state`.

Stop before: unexpected product edits, branch switch outside precondition, commit/push, secrets, unplanned network.

### Deterministic helper utilities

See [`scripts/README.md`](../scripts/README.md). **Public API:** `run-dp`. Internal: `dp_job_start.py`, `dp_job_close.py`, `render_jobs.py`, `validate_jobs_v4.py`.

For Python validation on Python changes: user command > project docs > dev-process default (`uv run ruff` / `.venv` when appropriate).

### Review-depth preset selection

[review/presets.md](../review/presets.md) — canonical preset definitions.
