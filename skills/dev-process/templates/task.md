# Task: [short title]

- **Dev process skill version:** v3
- **Task ID:** `[YYYYMMDD_short-slug]` (date first, e.g. `20260509_bounded-goal-dev-process`)
- **Owner / channel:** [optional]
- **Repo:** [path or name]
- **Links:** [issues, PRs]

## Intent

[One paragraph]

## Stage pointer

Current stage should mirror `state.yaml` → `current_stage`.

At task root, maintain append-only **`artifacts.timeline`** / **`artifacts.rework_log`** (task-root numbering: `skills/dev-process/artifacts/SKILL.md` § Numbered task-root artifacts; start from [timeline.md](timeline.md) and [rework_log.md](rework_log.md) in this folder).

Pipeline order: dev-process orchestrator skill at `skills/dev-process/SKILL.md` (this template is copied under `.hermes/tasks/<task-id>/`, so do not use `../` links to the skill tree—they break after copy).
