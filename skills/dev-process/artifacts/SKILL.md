---
name: dev-process-artifacts
description: >-
  Task-local artifact paths, numbering rules, persistence and git excludes, review round layout,
  and state.yaml synthesis pointers. Use when materializing or updating `.hermes/tasks/` files.
---

# Task artifacts (`dev-process`)

## Artifact root

Store **per-task working state** (not the project’s long-lived source of truth) under:

```text
.hermes/tasks/<task-id>/
```

Use templates from [templates/](../templates/). Copy [templates/state.yaml](../templates/state.yaml) and update fields as stages complete.

### Task id

- **Task directory name** = **`task_id`**. When **agent-generated**, prefer **`YYYYMMDD_<short-slug>`** (date first); use the same value in branch names such as `dev-process/<task_id>` unless the human directs otherwise. When the human **explicitly** supplies `task_id`, use it as given (see [goal/SKILL.md](../goal/SKILL.md)), subject to safety and filesystem constraints.

### Numbered task-root artifacts

Task-root Markdown artifacts (files directly under `.hermes/tasks/<task-id>/`, **not** under `reviews/`) use:

```text
NNNN_<stem>.md
```

**`state.yaml` → `artifacts.<key>`** holds the **current** filename for that logical artifact. **`state.yaml` itself is not numbered**—only the Markdown files use prefixes.

**Rules**

- If **`artifacts.<key>` is empty** (`""`), this is the **first materialization** of that logical artifact: compute the next prefix as **`max` of existing four-digit prefixes on task-root `NNNN_*.md` + 1** (see below; if none exist, max = −1 → **`0000_…`**), create **`NNNN_<stem>.md`**, and set **`artifacts.<key>`** to that filename in the **same session** as the file write.
- The **next** numeric prefix for any **new** numbered task-root file is **`max` of all existing four-digit prefixes** on files matching `NNNN_*.md` **in the task root** (not under `reviews/`), **plus 1**. If no such files exist yet, treat the max as **−1** so the first file uses **`0000_…`**.
- **If the artifact you are updating is already the highest-numbered** task-root file (its `NNNN` equals that max), you may **edit that file in place** and keep the same `artifacts.<key>` path.
- **If any other task-root file has a higher `NNNN`** than the file pointed to by `artifacts.<key>` for this logical artifact, **do not** overwrite that older file for a **material revision**: create a **new** file with the **next** id (`max + 1`) and **update `artifacts.<key>`** to the new filename. **Material revision** means a change that affects **decisions, approvals, plans, review outcomes, or handoff context**. **Minor typo or formatting-only** fixes may **update the bound file in place** even when a higher-numbered task-root file exists, unless project policy says otherwise.
- **Append-only task artifacts** — normally **append in place** to the file already recorded in `artifacts.*`, even when that file is **not** the highest-numbered task-root artifact. Kinds: **`artifacts.timeline`** (append-only event log), **`artifacts.rework_log`** (append-only rework log), **`artifacts.model_usage`** (append-only model usage record). Create a **new** numbered file only when **intentionally versioning** or replacing the artifact (human-agreed or documented policy).
- **`artifacts.model_usage`** — copy [templates/model_usage.md](../templates/model_usage.md) column layout; append rows via `dp_stage_boundary.py --print-markdown-row` ([scripts/README.md](../scripts/README.md)). Review files under `reviews/` must **not** use `NNNN_` prefixes or consume task-root numbering slots.
- **`validate_state.py` passing does not prove hygiene** — manually check that task-root `NNNN_` gaps are not invented, `artifacts.*` pointers match files, and model_usage rows use the compact template columns.
- **Do not renumber** or rename existing numbered task-root files to “fill gaps” or reorder history.

**Review artifacts** are separate: they live under **`reviews/<stage>/round_NN/`** and **do not** use `NNNN_` prefixes—use conventional names such as `requirements.md`, `architecture.md`, `synthesis.md` (see [review/SKILL.md](../review/SKILL.md)).

Legacy tasks may still use older flat names (`spec.md`, etc.); migrate with human agreement and consistent `artifacts` pointers.

See **Artifact persistence policy** below for Git and “promotion” to project docs.

## Artifact persistence policy

`.hermes/tasks/<task-id>/` holds **temporary dev-process task artifacts**—a **working log** for that development task only. These files support agents and humans *during* the task; they are **not** the project’s authoritative specification, design, or product record.

By default:

- **Do not commit** `.hermes/tasks/` artifacts to the **project** repository.  
- If a specification or design **must** become project documentation, create a **separate** project-level artifact (for example under `docs/`) intentionally curated for readers—**do not** promote `.hermes/tasks/…` paths **as-is** into canonical project docs without review and rewriting as needed.

**Do not add `.hermes/`** to the project’s tracked **`.gitignore`**: that is shared project policy and would affect collaborators who never use Hermes.

To exclude `.hermes/` locally without touching the repo’s `.gitignore`, use either:

**Global exclude (recommended on personal workstations):**

```bash
mkdir -p ~/.config/git
touch ~/.config/git/ignore
grep -qxF '.hermes/' ~/.config/git/ignore || echo '.hermes/' >> ~/.config/git/ignore

git config --global core.excludesfile ~/.config/git/ignore
```

Verify:

```bash
git config --global core.excludesfile
cat ~/.config/git/ignore
```

**This repository only (not committed)—`info/exclude`:**

```bash
EXCLUDE_FILE="$(git rev-parse --git-path info/exclude)"
grep -qxF '.hermes/' "$EXCLUDE_FILE" || echo '.hermes/' >> "$EXCLUDE_FILE"
```

**Contrast:**

| Location | Role | Typical Git handling |
|---------|------|------------------------|
| `skills/dev-process/` (this skill) | Process rules & templates | Version in the Hermes-home / skill repository |
| `<project>/.hermes/tasks/<task-id>/` | Task working log | **Do not commit** to project repo by default (see excludes above) |
| `<project>/docs/…` (or similar) | Optional **formal** project specs | Version in project repo when the team wants durable docs |

Append-only history (task root):

- [templates/timeline.md](../templates/timeline.md) → `artifacts.timeline` (filename follows § **Numbered task-root artifacts** on first materialization) — chronological log of stages and artifacts.  
- [templates/rework_log.md](../templates/rework_log.md) → `artifacts.rework_log` (same) — each blocking rework: source synthesis, owner, artifacts changed, rerun rounds.
- [templates/model_usage.md](../templates/model_usage.md) → `artifacts.model_usage` — stage / preset / reasoning effort / session evidence for recording model cost attribution vs dev-process lifecycle ([validation/SKILL.md — Model usage](../validation/SKILL.md#model-usage)).

## Review outputs by stage

Review rounds use **round-numbered** directories (`round_01`, `round_02`, …) as described below.

**Never overwrite** prior review outputs. Each review run writes under a **new** directory:

```text
reviews/<stage>/round_NN/
```

Use **two‑digit** `NN` (`round_01`, `round_02`, …); extend width if rounds exceed 99.

Within each `round_NN/`, use **unprefixed** conventional filenames (e.g. `requirements.md`, `architecture.md`, `synthesis.md`) per [review/SKILL.md](../review/SKILL.md) and the standard recipes—**not** `NNNN_` prefixes (those apply only to **task-root** artifacts).

Example layout:

```text
reviews/
  spec/
    round_01/
      requirements.md
      architecture.md
      synthesis.md

  plan/
    round_01/
      architecture.md
      checklist_compliance.md
      impact.md
      synthesis.md
    round_02/
      ...

  test/
    round_01/
      requirements.md
      test_quality.md
      checklist_compliance.md
      synthesis.md

  implementation_phase_01/
    round_01/
      checklist_compliance.md
      diff_detail.md
      architecture.md
      synthesis.md
    round_02/
      ...

  final/
    round_01/
      architecture.md
      diff_detail.md
      impact.md
      naming_doc.md
      test_quality.md
      synthesis.md
```

**Latest synthesis pointers (`state.yaml`):** maintained by the **synthesis-role** agent (Orchestrator fallback when synthesis is skipped)—**humans should not routinely edit these** when using the normal workflow. v1 has no daemon; updates happen in the same session as synthesis.

- After each completed review round, the **synthesis-role** agent (`review/agents/synthesis.md`) **must** update `review_rounds` for that stage and set `latest_reviews.<stage>` to that round’s **`synthesis.md`** path (e.g. `reviews/spec/round_01/synthesis.md`) in the **same session** as writing that file.  
- If a team **skips synthesis** for a stage (allowed only where the router says optional), the **Orchestrator** (the agent/session coordinating handoff) performs the equivalent `review_rounds` / `latest_reviews` update and records why in **`artifacts.timeline`**.  

Detail: [review/SKILL.md — Who updates state.yaml](../review/SKILL.md#who-updates-stateyaml).

**Optional shortcut:** under e.g. `reviews/final/`, `latest.md` may summarize “latest round directory + status” for humans (manual or agent-updated **v1**: no symlink automation required).

Details: [review/SKILL.md — Review rounds and rework history](../review/SKILL.md#review-rounds-and-rework-history).

Use **output formats** from `review/templates/review_result.md` (per reviewer file) and `review/templates/synthesis_result.md` (for `synthesis.md`).
