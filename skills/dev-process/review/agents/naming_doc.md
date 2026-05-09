# Review agent: naming_doc

## Objective

Consistency and clarity of names, comments, and user-visible documentation touched by change.

## Checklist

- [ ] Names match domain vocabulary already in repo/spec.  
- [ ] Comments explain **why** when non-obvious; avoid stale comments contradicting code.  
- [ ] README / docs references updated where users would look.  
- [ ] Breaking changes surfaced in changelog or notices if required by repo convention.

## Output

Use [`../templates/review_result.md`](../templates/review_result.md). Prefer **non-blocking** for pure style; **blocking** only when mismatches confuse API contracts or contradict spec.
