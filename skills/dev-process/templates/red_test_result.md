# Red test result — [task title]

Recorded **during the test stage**, **before** product implementation begins. This file is copied from `templates/red_test_result.md`.

**Task ID:** `[YYYYMMDD_short-slug]`  
**Date:** `[ISO date]`

## Context

- Link **`artifacts.plan`** (filename from `state.yaml` → `artifacts.plan`) red-test expectation (or documented waiver).

## Command(s) run

```bash

```

## Outcome

- [ ] Tests failed as expected (red)  
- [ ] Unexpected failure (describe — may block implementation or require test/plan fix)  
- [ ] N/A — justified in **`artifacts.plan`**; point to alternate verification

## Notes

Evidence snippets, failing test names, short logs (bounded).

## Alternative

If the team prefers a single file, put this content under a **## Red test results** heading inside **`artifacts.test_implementation`** instead—but keep it **within the test stage**, not implementation logs.
