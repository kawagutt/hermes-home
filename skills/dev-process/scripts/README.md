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
