# Review agent: test_quality

## Objective

Assess whether tests **credibly defend** declared behavior without undue brittleness.

## Checklist

- [ ] Tests fail for wrong reasons absent (avoid tautologies).  
- [ ] Stable vs volatile surfaces: prefer public contracts over internals unless justified.  
- [ ] Fixtures and setup complexity proportionate to value.  
- [ ] Negative / edge paths covered where risks warrant.  
- [ ] Flaky patterns avoided (sleeps, unordered collections without sorting, clocks without control).

## Output

Use [`../templates/review_result.md`](../templates/review_result.md). **Blocking** if tests omit critical protections or falsely pass.
