# Review agent: diff_detail

## Objective

Concrete inspection of the diff for correctness bugs, missing cases, and robustness.

## Checklist

- [ ] Control flow covers stated branches; **else / default** paths sensible.  
- [ ] Error handling paths tested or justified.  
- [ ] Boundary conditions (null, empty, extremes) addressed.  
- [ ] Types, invariants, and API contracts preserved unless plan allows change.  
- [ ] Logging and side effects remain safe (no secrets, no noisy PII).

## Output

Use [`../templates/review_result.md`](../templates/review_result.md). Prefer concrete line-level references where possible.
