# Task: [short title]

- **Dev process skill version:** v1
- **Task ID:** `[YYYY-MM-DD-or-slug]`
- **Owner / channel:** [optional]
- **Repo:** [path or name]
- **Links:** [issues, PRs]

## Intent

[One paragraph]

## Stage pointer

Current stage should mirror `state.yaml` → `current_stage`.

At task root, maintain append-only **[`timeline.md`](timeline.md)** and **[`rework_log.md`](rework_log.md)** (start from the templates of the same names in this folder).

Pipeline order: dev-process orchestrator skill at `skills/dev-process/SKILL.md` (this template is copied under `.hermes/tasks/<task-id>/`, so do not use `../` links to the skill tree—they break after copy).
