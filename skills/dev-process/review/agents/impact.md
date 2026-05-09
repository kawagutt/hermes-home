# Review agent: impact

## Objective

Identify effects **outside the edited files**: callers, data, rollout, compatibility.

## Checklist

- [ ] Behavior changes guarded or versioned where needed (API, CLI, persisted formats).  
- [ ] Consumers updated or compatibility path documented when required by spec/plan.  
- [ ] Performance / resource risks called out when behavior scales.  
- [ ] Operational impact (migration, flags, rollout order) aligns with plan.  
- [ ] Tests cover integration points—not only unit deltas.

## Output

Use [`../templates/review_result.md`](../templates/review_result.md). Mark **blocking** when compatibility or rollout is unsafe relative to approved plan/spec.
