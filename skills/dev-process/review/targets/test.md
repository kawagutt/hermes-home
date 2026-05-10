# Review target: test

## Scope

Review **tests and test-planning artifacts** after plan approval—not product code correctness beyond what tests assert.

## Inputs (typical)

- **`artifacts.spec`**, **`artifacts.plan`**  
- Authored/modified tests, **`artifacts.test_plan`**, **`artifacts.test_implementation`**, **`artifacts.red_test_result`** if present  

## Out of scope

- Detailed implementation internals not required by approved plan/spec  

## Review focus areas (routing hints)

- Traceability to success criteria (`requirements`)  
- Assertion strength and coupling (`test_quality`, `checklist_compliance`)
