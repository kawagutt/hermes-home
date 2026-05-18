# Review agent: checklist_compliance

## Objective

Verify adherence to **`artifacts.phase_checklists` / plan constraints** — primary gatekeeper for **“may we proceed to next phase?”**

## Checklist

- [ ] Allowed changes list satisfied; forbidden changes clean.  
- [ ] Explicit validation commands for the phase were run / recorded appropriately.  
- [ ] Scope creep indicators absent ( unrelated formatting, unrelated refactors ).  
- [ ] Artifact updates (`phase_results.md`, logs) consistent with claimed progress.  

## Output

Use [`../templates/review_result.md`](../templates/review_result.md). **Blocking** if phase constraints violated or checks missing without approved waiver in plan/spec trail.

## Special role

For **plan** target: confirm plan is reviewable, phased, and testable per checklists; **no implementation phase marked `heavy` without split or documented waiver**; each phase has matched checklist section, allowed files, and validation commands per `skills/dev-process/plan/SKILL.md` § **Implementation phase sizing**.  
For **test** target: confirm tests align with planned validation strategy.  
For **implementation_phase** target: **hard stop** if compliance fails before advancing.
