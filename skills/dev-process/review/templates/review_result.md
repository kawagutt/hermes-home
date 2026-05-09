# Review result template

Replace `TITLE` / bracketed fields. File name matches agent role (e.g. `architecture.md`).

## Review stage

- Task ID: `[task-id]`  
- Target: `[spec | plan | test | implementation_phase | final_diff]`  
- Review round: `[round_01]` — directory under `reviews/<stage>/`; never overwrite prior rounds.  
- Agent: `[requirements | architecture | diff_detail | impact | naming_doc | test_quality | checklist_compliance]` — **not** synthesis; synthesis uses [`synthesis_result.md`](synthesis_result.md).  
- Date: `[ISO date]`  

## Summary

[2–5 sentences]

## Findings

| ID | Severity | Classification | Description | Evidence / location |
|----|----------|----------------|-------------|---------------------|
| F1 | high/med/low | blocking / non-blocking / question / suggested follow-up | | |

(Add rows as needed.)

## Notes

[Any scope limits, missing context requests, or follow-ups]
