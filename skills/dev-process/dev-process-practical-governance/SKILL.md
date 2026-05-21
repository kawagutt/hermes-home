---
name: dev-process-practical-governance
description: >-
  Supplemental practical governance lessons for Hermes dev-process runs: helper-environment dependency boundaries, documented evidence deviations, and final approval without committing.
---

# Dev-process practical governance

Use this with `dev-process` when final-gate approval, validation helpers, or governance evidence has practical environment complications. Prefer canonical `dev-process-*` skills when they are patchable; this skill captures class-level pitfalls learned from real runs.

## Helper environment dependency boundaries

When a dev-process helper script fails because its own runtime lacks a package such as `PyYAML`, classify it as a **dev-process helper environment issue** unless the project product/tests actually import that package.

Do this instead of polluting the project dependency set:

1. Record the exact helper command and error in the current gate/timeline artifact.
2. State clearly whether project product code/tests need the package.
3. If they do not, do **not** add it to the project `pyproject.toml` solely for Hermes helpers.
4. Update helper documentation or run the helper-environment preflight (`check_helper_env.py`) so the boundary is visible in future tasks.
5. If helper validation could not run, say so explicitly and do not claim strict helper-based validation; use manual inspection only as a documented fallback.

## Final approval with “leave uncommitted”

If the final human gate option explicitly approves the result while leaving changes uncommitted:

1. Update the current bound final gate artifact in place with the approval decision.
2. Set `approved.final_human_gate: true`, clear `pending_human_gate`, and move `current_stage` to `completed`.
3. Append the approval to the timeline.
4. Verify/report `git status --short --branch`.
5. Do **not** ask a second commit/merge question and do **not** commit, push, or merge.

## Known overlap

This should eventually be folded into:

- `dev-process-human-gates` — final approval behavior and no second commit prompt.
- `dev-process-validation` — helper environment dependency boundaries and no strict-validation claims after helper failure.
- `dev-process-session-learnings` — broader session-learned governance pitfalls.
