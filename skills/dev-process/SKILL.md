---
name: dev-process
description: Runs a structured software development process with spec, plan, implementation, tests, and independent reviews.
---

# Dev Process

This skill manages a structured software development process.

## Modules

- spec: clarify requirements, non-goals, risks, and success criteria.
- plan: create implementation phases, checklists, validation commands, and reviewer assignments.
- implementation: implement according to the approved plan and phase checklists.
- review: run independent reviews from multiple perspectives and synthesize findings.

These modules are process capabilities, not strictly sequential phases. Review may happen during spec, plan, and implementation.

## Safety Rules

- Do not commit unless explicitly requested.
- Do not push.
- Do not modify files outside the current repository.
- Do not run destructive git commands.
- In spec, plan, and review modules, do not edit product code.
- Prefer targeted checks before broad checks.

## Context Rules

For review, pass only:
- approved spec
- approved plan
- current git diff
- test results
- relevant files

Do not pass implementation rationale unless explicitly requested.

## Output

Store artifacts under `.hermes/tasks/<task-id>/`.
