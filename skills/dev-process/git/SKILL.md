---
name: dev-process-git
description: >-
  Dev-process task branch rules, precondition updates, commits allowed on the task branch, and git
  safety constraints. Use when creating or switching branches, recording branch state in state.yaml,
  or deciding what git operations each role may perform.
---

# Git and task branch (`dev-process`)

## Task branch and commits

Before asking for `human_spec_gate` approval, check whether a **new branch can be created** for this task (or whether the human will explicitly direct use of a specific branch) and record the result in `state.yaml` → `branch` and gate artifacts.

After **plan review** completes, satisfy the **task branch precondition** **before test implementation**: create the dedicated task branch for this task, or switch to the branch dev-process **already created** for this task.

**Branch rule (canonical):** all test and product work for the task must happen **only** on the dedicated branch **created by dev-process for this task**. Do not use any pre-existing branch for task work unless the human **explicitly** instructs it.

After creating or switching to the task branch, the **Orchestrator** must update, in the **same session**:

- `state.yaml` → `branch.name`
- `state.yaml` → `branch.task_branch_precondition_met`
- `state.yaml` → `branch.commits_allowed_on_task_branch` (set consistent with the agreed task/plan policy for test and product commits on the task branch)

and append a row to **`artifacts.timeline`**: if **`artifacts.timeline`** is empty, **first materialize** the timeline file per [artifacts/SKILL.md — Numbered task-root artifacts](../artifacts/SKILL.md#numbered-task-root-artifacts) (set `artifacts.timeline`, then append); if already bound, **append in place** to that file (do not create a new numbered timeline file for routine branch events—see **Append-only logs** in artifacts skill) with the branch name and the create/switch command used (or equivalent evidence).

TestAuthorAgent and ImplementationAgent may **commit** only on that task branch. **Merges** and **pushes** (and commits to any other branch) are forbidden unless the human explicitly requests them. `.hermes/tasks/<task-id>/` artifacts remain uncommitted working logs by default. Never mix “product/test commits on the task branch are allowed” with “task artifacts may be committed.”

## Safety rules (git-related)

Summarized here; orchestrator overview: [SKILL.md — Safety rules](../SKILL.md#safety-rules).

- Do not **push**, **merge**, or **commit** outside the dev-process-created task branch for this task unless explicitly requested.
- Product and test commits are allowed **only** on the dev-process-created task branch. Commits to other branches, merges, and pushes remain forbidden unless explicitly requested.
- Do not modify **existing** git-untracked product/project files unless explicitly instructed. Creating **new** product or test files is allowed only when the approved plan lists them or clearly permits them.
- Do not modify files outside the current repository.
- Do not run destructive git commands.
