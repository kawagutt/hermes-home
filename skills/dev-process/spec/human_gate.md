# Human spec gate

## Purpose

Confirm shared understanding of the spec **before** planning. This reduces expensive drift in plan, tests, and implementation.

This is **not** a quiz to “test the human.” It is a **read-back** to catch misinterpretation.

## When

After **spec review** outputs exist and before creating or locking `plan.md`.

## Before moving to plan, the human must confirm

1. **Goal** — Can you state the task’s purpose in one sentence?  
2. **Non-goal** — Do you understand what we are **not** doing this round?  
3. **Success criteria** — Do you know what “done” means in verifiable terms?  
4. **Main risk** — What is the most dangerous failure mode, and is it captured?  
5. **Approval** — May we proceed to plan with this spec?

## Artifact

Record answers in `.hermes/tasks/<task-id>/human_spec_gate.md` using [templates/human_spec_gate.md](../templates/human_spec_gate.md).

If any item is “no” or uncertain, resolve by updating `spec.md` or documenting an explicit decision before planning.
