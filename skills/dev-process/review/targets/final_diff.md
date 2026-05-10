# Review target: final_diff

## Scope

Holistic assessment at **merge time**: full intended change set vs spec/plan/tests.

## Inputs (typical)

- **`artifacts.spec`**, **`artifacts.plan`**, **`artifacts.test_plan`**  
- Final comprehensive diff (or PR diff)  
- **`artifacts.final_test_result`** (see [templates/final_test_result.md](../../templates/final_test_result.md); path from `state.yaml`) / CI output if captured  
- Prior per-stage reviews (optional summaries)  

## Out of scope

- Re-arguing settled spec unless new evidence contradicts  

## Focus (routing hints)

- Architectural integrity, edge cases, impact beyond diff, naming/docs, test sufficiency—per assigned agents
