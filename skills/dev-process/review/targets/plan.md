# Review target: plan

## Scope

Review **`artifacts.plan`**, **`artifacts.phase_checklists`**, and validation strategy **after spec gate**, before tests.

## Inputs (typical)

- Approved **`artifacts.spec`**, latest `reviews/spec/round_NN/synthesis.md` (or `state.yaml` → `latest_reviews.spec`), **`artifacts.human_spec_gate`**  
- **`artifacts.plan`**, **`artifacts.phase_checklists`**  

## Out of scope

- Product implementation diffs (not yet authoritative)  

## Review focus areas (routing hints)

- Phasing size and sequencing  
- Alignment with forbidden changes  
- Practical validation commands vs environment  
- Whether tests can realistically be authored from spec + plan  

## Orchestrator linkage

Orchestrator enforces:

```text
Do not start test implementation until plan review is complete.
If plan review has blocking findings or escalation triggers, stop.
```
