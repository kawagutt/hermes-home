# Phase checklists

Duplicate or adapt per phase from `plan.md`. One section per phase.

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
- Branch precondition before product implementation: `[agent-created task branch / repository policy]`
- Commit policy: commits allowed only on the agent-created task branch; no commits to other branches, merges, or pushes unless explicitly requested.
- Git-untracked file policy: do not modify untracked product/project files without explicit human permission; if not instructed, leave them alone.
- Notes on artifact policy: `.hermes/tasks/` remains uncommitted by default.
