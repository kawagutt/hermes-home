# Review target: spec

## Scope

Review the task specification (**`artifacts.spec`**; path from `state.yaml`) **before** plan or code.

## Inputs (typical)

- `.hermes/tasks/<task-id>/` + `artifacts.spec`  
- Minimal repo context only if needed to interpret terms (bounded)  

## Out of scope

- Implementation drafts  
- Detailed file-level plans (belongs to plan target)  

## Review focus areas (routing hints)

Pointing reviewers—not a checklist duplicate:

- Goals vs non-goals consistency  
- Testable success criteria  
- Risks and unknowns surfaced for planning  

Agents apply their detailed lists from `review/agents/*.md`.
