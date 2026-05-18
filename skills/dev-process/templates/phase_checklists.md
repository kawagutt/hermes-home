# Phase checklists

Duplicate or adapt per phase from **`artifacts.plan`** (path from `state.yaml`). **One section per implementation phase** — scope must match the plan row (allowed files, validation, checklist count). Do not widen a checklist beyond its plan phase; split the plan first per `skills/dev-process/plan/SKILL.md` § **Implementation phase sizing**.

## Phase 1: [name]

### Allowed changes

- 

### Forbidden changes

- 

### Checklist

- [ ] 
- [ ] 

### Validation

```bash
# commands
```

### Rollback / notes

- 

---

## Phase 2: [name]

(Repeat structure)


## Per-phase validation slots

For each implementation phase, record:

- Selected validation command(s): `[command]`
- Python/Ruff command if Python files change: `[command or project-policy exception]`
- Branch feasibility checked before spec human gate: `[yes/no + evidence]`
- Task branch precondition after plan review, before test implementation: `[dev-process task branch name; same branch for test and product work per SKILL.md]`
- Commit policy: TestAuthorAgent may commit test changes and ImplementationAgent may commit product changes only on the dev-process task branch for this task; no commits to other branches, merges, or pushes unless explicitly requested.
- Git-untracked file policy: do not modify **existing** untracked product/project files unless explicitly instructed; new product/test files are allowed only when the approved plan lists or clearly permits them; `.hermes/tasks/<task-id>/` is exempt but remains uncommitted by default.
- Notes on artifact policy: `.hermes/tasks/` remains uncommitted by default.
