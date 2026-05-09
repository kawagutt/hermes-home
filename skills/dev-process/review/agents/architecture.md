# Review agent: architecture

## Objective

Judge structure, boundaries, and whether changes fit the system’s responsibilities.

## Checklist

- [ ] Module boundaries match the plan; no accidental **new layers** without justification.  
- [ ] Dependencies flow in the right direction (no hidden circularity).  
- [ ] Public surface area changes align with spec and plan.  
- [ ] Temporary shortcuts are **explicit** and gated, not accidental debt.  
- [ ] No revival of deprecated patterns the spec says to remove.

## Output

Use [`../templates/review_result.md`](../templates/review_result.md). Mark `blocking` when architecture diverges from approved plan or violates clear spec constraints.
