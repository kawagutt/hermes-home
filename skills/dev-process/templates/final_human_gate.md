# Final human gate

Task ID: `[YYYYMMDD_short-slug]`  
Date: `[ISO date]`  
Human: `[name or handle]`

Before merge/completion, review the final synthesis, validation evidence, and Japanese final summary.

## Inputs

- Final summary (Japanese): **`artifacts.final_summary_ja`** (path from `state.yaml`)
- Final review synthesis: `reviews/final/round_NN/synthesis.md`
- Final validation evidence: **`artifacts.final_test_result`** and/or **`artifacts.phase_results`** (paths from `state.yaml`)
- Current diff / PR / branch status: `[link or command output]`

## Decision checklist

### Git governance confirmation

- [ ] Any commit will be made only on the dev-process-created task branch for this task (or on a pre-existing branch only if explicitly instructed and recorded).
- [ ] No commits to other branches, merges, or pushes are approved unless explicitly stated here.
- [ ] **Existing** git-untracked product/project files were not modified without explicit instruction; any new files match the approved plan.


- [ ] The final diff matches the approved **`artifacts.spec`** and **`artifacts.plan`**.
- [ ] Required tests / validations passed, or accepted exceptions are documented.
- [ ] Blocking review findings are resolved.
- [ ] Remaining non-blocking findings are accepted or assigned as follow-up.
- [ ] The task is ready for the human-controlled commit / merge / completion decision.

## Required human decisions

If the final summary contains `Required human decisions`, present those items **one by one in chat** before asking for final approval. For each item, record the decision question, recommendation, practical consequences, whether it blocks completion/merge, and the artifact section to update. The gate artifact records the discussion; it is not a substitute for the discussion.

## Approval

A short CUI response such as `OK` is acceptable only after the concise Japanese summary has been provided and after any required decision items have been presented individually with an opportunity for the human to answer or discuss them. Do not collapse multiple required human decisions into a single generic `OK` prompt.

Human response:

> 

Recorded interpretation:

- [ ] Approved for human-controlled commit / merge / completion.
- [ ] Not approved; comments below require rework.

## Comments / follow-up

> 

## Artifact policy reminder

`.hermes/tasks/<task-id>/` artifacts are task-local working logs and are not committed by default, even when product/project commits are allowed on the task branch.
