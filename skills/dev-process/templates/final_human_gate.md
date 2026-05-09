# Final human gate

Task ID: `[task-id]`  
Date: `[ISO date]`  
Human: `[name or handle]`

Before merge/completion, review the final synthesis, validation evidence, and Japanese final summary.

## Inputs

- Final summary (Japanese): `final_summary_ja.md`
- Final review synthesis: `reviews/final/round_NN/synthesis.md`
- Final validation evidence: `final_test_result.md` and/or `phase_results.md`
- Current diff / PR / branch status: `[link or command output]`

## Decision checklist

### Git governance confirmation

- [ ] Any commit will be made only on a branch the agent created for the task.
- [ ] No commits to other branches, merges, or pushes are approved unless explicitly stated here.
- [ ] Git-untracked product/project files were not modified without explicit human permission.


- [ ] The final diff matches the approved `spec.md` and `plan.md`.
- [ ] Required tests / validations passed, or accepted exceptions are documented.
- [ ] Blocking review findings are resolved.
- [ ] Remaining non-blocking findings are accepted or assigned as follow-up.
- [ ] The task is ready for the human-controlled commit / merge / completion decision.

## Approval

A short CUI response such as `OK` is acceptable after the concise Japanese summary has been provided.

Human response:

> 

Recorded interpretation:

- [ ] Approved for human-controlled commit / merge / completion.
- [ ] Not approved; comments below require rework.

## Comments / follow-up

> 

## Artifact policy reminder

`.hermes/tasks/<task-id>/` artifacts are task-local working logs and are not committed by default, even when product/project commits are allowed on the task branch.
