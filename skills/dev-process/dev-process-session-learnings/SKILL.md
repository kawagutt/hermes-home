---
name: dev-process-session-learnings
description: >-
  Supplemental class-level lessons for Hermes dev-process sessions when the main dev-process
  category skill files cannot be patched directly via skill_manage. Covers phase-boundary rework,
  evidence deviations at gates, and inspectable artifact discipline.
---

# Dev-process session learnings

Use this as a supplemental dev-process reference when operating the staged pipeline. It intentionally overlaps with `dev-process-implementation` and `dev-process-human-gates`; prefer those canonical skills when they become patchable.

## Phase-boundary self-check during implementation

During implementation, continuously compare the approved phase scope against what the RED tests and public behavior require.

If implementation discovers the approved phase boundary is wrong—for example, RED tests exercise a public CLI entrypoint but the plan puts CLI wiring in a later phase—do **not** silently treat the mismatch as “close enough.” Instead:

1. Stop product work at the mismatch.
2. Route to PlanAgent.
3. Revise `artifacts.plan` and `artifacts.phase_checklists` with a new numbered artifact when appropriate.
4. Record `artifacts.rework_log` and timeline entries.
5. Rerun at least a focused plan review and synthesis.
6. Resume implementation only after the revised plan review recommends Proceed.

## Evidence deviations at final human gates

When final review says the product behavior can proceed but governance/model/reviewer session evidence is incomplete:

- Do not claim a strict pass.
- Record the evidence gap in `artifacts.model_usage`, review manifests, final synthesis, final summary, and final gate artifact.
- Present it as a separate required human decision before generic final approval.
- If the human accepts it, describe completion as a documented known deviation/waiver, not strict evidence compliance.
- If the human rejects it, rerun the affected review/model-usage steps with verifiable evidence.

## Artifact and docs discipline for public CLI tasks

For public CLI/data-contract changes:

- RED tests should exercise the public command path if the user-facing contract is CLI behavior.
- Keep helper logic in a module and CLI wiring thin.
- Validate examples with cheap parse/smoke checks even when end-to-end rendering is out of scope.
- If examples use assets, record provenance and avoid external-download dependencies.

## Overlap note

This supplemental skill should eventually be folded into:

- `dev-process-implementation` — phase-boundary self-check and plan rework.
- `dev-process-human-gates` — evidence deviation as one-by-one required decision before final approval.
- `dev-process-validation` — model/session evidence gaps and waiver recording.
