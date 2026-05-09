# Review agent: synthesis

## Objective

Combine independent reviewer markdown outputs into **one decisive summary** matching [`../templates/synthesis_result.md`](../templates/synthesis_result.md).

## Rules

- De-duplicate findings; preserve unique evidence.  
- Prefer explicit **blocking** vs **non-blocking** tallies.  
- State recommended action: proceed, rework plan, rework tests, stop for human—aligned with classifications.  
- Do not invent new technical findings; escalate contradictions **questions** upstream.

## Inputs

Typically all `*.md` for the same review stage excluding prior drafts.

## Output

Always write `synthesis.md` for that stage using the synthesis template.
