# Review target: implementation_phase

## Scope

Checkpoint after **one planned phase** of product implementation (not the whole feature unless single-phase).

## Inputs (typical)

- Approved spec/plan/checklists  
- Git diff limited to phase scope (or instructed paths)  
- Test/lint outputs for that phase  
- `phase_results.md` entry  

## Focus (routing hints)

- **checklist_compliance:** phase gates and forbidden edits  
- **diff_detail:** local correctness hazards  
- **architecture:** layering and unintended coupling  

## Output directory

`.hermes/tasks/<task-id>/reviews/implementation_phase_NN/round_MM/` (phase `NN` matches plan; `round_MM` increments per checkpoint review)
