# dev-process helper scripts

These helpers are small, deterministic, local tools for reducing mechanical process mistakes. They are **not** a workflow engine and do not replace role judgment, reviewer synthesis, human gates, or approved plans.

Helpers may update task-local artifacts only. They must not push, merge, commit, or edit product code.

## Dependencies

The Python helpers require `PyYAML` (`import yaml`). Use the repository environment if available; otherwise install it in the active environment before running helpers.

Example:

```bash
python3 -m pip install PyYAML
```

## `validate_state.py`

```bash
python3 skills/dev-process/scripts/validate_state.py .hermes/tasks/<task-id>
```

Checks:

- `task_id` matches the task directory name.
- non-empty artifact pointers exist.
- task-root Markdown artifacts use `NNNN_<stem>.md` numbering.
- task-root Markdown files are not unnumbered ad-hoc artifacts.
- `latest_reviews.<stage>` paths exist and match `reviews/<stage>/round_NN/synthesis.md`.
- `review_rounds.<stage>` matches the `round_NN` in `latest_reviews.<stage>`.
- `review_rounds=0` does not have a misleading latest review pointer.
- required branch fields exist.

State comment policy: helpers that write `state.yaml` use PyYAML and may drop YAML comments. Dev-process state comments are template guidance, not persistent task data. Preserve durable process notes in task Markdown artifacts (`timeline`, gates, review synthesis), not as YAML comments in `state.yaml`.

## `review_round.py`

```bash
python3 skills/dev-process/scripts/review_round.py .hermes/tasks/<task-id> <stage> --dry-run
python3 skills/dev-process/scripts/review_round.py .hermes/tasks/<task-id> <stage> --create
python3 skills/dev-process/scripts/review_round.py .hermes/tasks/<task-id> <stage> --finish
```

Semantics:

- `--create` creates only the next `reviews/<stage>/round_NN/` directory.
- `--create` does **not** update `review_rounds` or `latest_reviews`.
- `--finish` requires a non-placeholder `synthesis.md` containing a `## Recommendation` section, then updates `review_rounds.<stage>` and `latest_reviews.<stage>`.

This preserves the meaning of `review_rounds`: completed review rounds, not merely created directories.

## `branch_precondition.py`

Verifies and records that the task branch precondition is satisfied. It does **not** create or switch branches.

```bash
git switch -c dev-process/<task-id>
python3 skills/dev-process/scripts/branch_precondition.py \
  .hermes/tasks/<task-id> dev-process/<task-id> \
  --apply --evidence 'git switch -c dev-process/<task-id>'
```

Timeline precondition: before `--apply`, `state.yaml -> artifacts.timeline` must point to an existing timeline file with the four-column template header `Time | Stage | Action | Output`. If the task has not materialized the timeline yet, materialize it first according to the numbered task-root artifact rules.

Behavior:

- Verifies the current git branch matches the requested task branch by default.
- Updates `branch.name`, `branch.task_branch_precondition_met`, and `branch.commits_allowed_on_task_branch`.
- Appends a 4-column timeline row: `Time | Stage | Action | Output`.
- Use `--dry-run` before `--apply`.
- `--skip-git-check` exists only for isolated tests and unusual manual recovery cases; routine use should verify the current git branch.

## `dp_hermes.py`

Resolves which **Hermes profile** (`dp-strong`, `dp-code`, `dp-cheap`, …) to use for a dev-process **action** or **`state.yaml` stage**, then optionally runs `hermes` with `--profile=…`. It **does not** modify global Hermes configuration.

**Policy file:** [`config/model_policy.yaml`](../config/model_policy.yaml) (`schema_version: 1`). Raw model IDs are **not** listed there — only logical roles and Hermes profile names.

**Prerequisites**

- PyYAML.
- Hermes CLI on `PATH` (override with `HERMES_EXE`).
- Hermes profiles named in `model_policy.yaml` → `profiles` values must exist (`hermes profile create dp-code --clone`, etc.).

**Hermes probe (normal launch only)**

| Mode | Runs `hermes --profile=…` probe? |
|------|-----------------------------------|
| `--print-profile-only` | **No** — policy resolution only (for CI / offline policy checks). |
| `--print-json` | **No** — same as above. |
| Default (launch Hermes) | **Yes** — before printing the model-usage line, runs `hermes --profile=<resolved_profile> version`. Fails with **exit 2** if this probe fails (verifies both CLI `--profile` support and that the **resolved** profile exists and works). |

**Exit codes**

| Cause | Exit code |
|-------|-----------|
| Policy/state resolution errors, probe failure before launch, invalid flags | **2** |
| Hermes subprocess (user command after `--`) | **Hermes’ exit code** (unchanged) |

**Invocation**

Arguments after a bare `--` are passed through to Hermes (avoids clashes with this script’s own flags):

```bash
python3 skills/dev-process/scripts/dp_hermes.py \
  --task-dir .hermes/tasks/<task-id> \
  --action write_tests \
  -- chat -q "hello"
```

If `--action` is omitted, resolution uses **`state.yaml` → `current_stage`** against `stage_defaults` (keys must match `current_stage` exactly, e.g. `implementation`, not `implement`). **`implement`** is only an `--action` name via `action_overrides`.

**Output**

- **Default (launch `hermes`):** prints exactly **one** model-usage line on **stdout**, then runs Hermes. The model-usage line and Hermes’ stdout are **concatenated on the same stream** — for machine-readable output without mixing, use **`--print-json`** (or `--print-profile-only`).
- **`--print-profile-only`:** stdout is **only** the resolved profile name (e.g. `dp-code`). No extra text. Errors and messages go to **stderr**.
- **`--print-json`:** stdout is **only** one JSON object (includes `resolution_source`: `action` or `stage`). Errors to stderr.

**State file**

Unless **`--record-state`** is passed, **`state.yaml` is never modified**. If **`--record-state`** is set: update `last_hermes_profile` / `last_dev_process_action` / `last_resolution_source` **only after Hermes exits 0** (so a failed launch does not update state). Print-only modes never write state. See template comments in `skills/dev-process/templates/state.yaml`.

When state is written, **PyYAML `yaml.dump()` rewrites the whole file** — inline comments and original formatting may be lost. Task `state.yaml` is a working artifact, so this is acceptable for Phase 1; avoid `--record-state` if you need to preserve manual comments.

**Tests**

```bash
python3 skills/dev-process/scripts/test_dp_hermes.py -v
```

Mostly uses `--print-profile-only` / `--print-json`; probe/launch paths are covered with a temporary fake `HERMES_EXE`.

**Strict errors (exit 2)**

Missing/invalid policy file, `schema_version` ≠ 1, empty `profiles` / `stage_defaults` / `action_overrides`, unknown `--action`, empty or unknown `current_stage` when `--action` is omitted, unknown logical role, empty Hermes profile string, **resolved-profile probe** failure (normal mode only), etc. **No silent fallback** from actions to stages.
