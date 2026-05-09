# Review agent: requirements

Use with targets **spec**, **test**, or **final_diff** where traceability matters.

## Objective

Verify the artifact **matches declared requirements and success criteria** without inventing new scope.

## Checklist

- [ ] Every **success criterion** maps to a test, check, or explicitly documented non-automated verification.  
- [ ] **Non-goals** are respected; no creeping scope in tests or final diff.  
- [ ] Required **user-visible** behavior in spec is exercised or explicitly deferred with rationale.  
- [ ] Contradictions across spec / plan / tests are absent or called out as **blocking**.

## Output

Use [`../templates/review_result.md`](../templates/review_result.md). Tag issues `blocking` when success criteria are unmet or ambiguous in a way that blocks verification.
