---
name: dev-process-spec
description: >-
  Produces task spec.md from goals, non-goals, success criteria, risks, and constraints; runs spec
  review via review router; captures human_spec_gate.md before plan. Use when authoring or
  revising specification for a Hermes dev-process task after loading dev-process.
---

# Spec stage

Produce and stabilize **what** to build before any implementation or test code work.

## Outputs

Primary artifact: `.hermes/tasks/<task-id>/spec.md` (**working spec** for this task; not canonical project documentation unless deliberately promoted—see orchestrator [SKILL.md](../SKILL.md#artifact-persistence-policy)).
Start from [templates/spec.md](../templates/spec.md).

After spec reviewer agents finish for this run, write outputs under `.hermes/tasks/<task-id>/reviews/spec/round_NN/` (see orchestrator round rules): per-agent files plus `synthesis.md`.

## Required content in `spec.md`

Include at minimum:

- Goal  
- Non-goals  
- User-visible behavior  
- Internal behavior (if any)  
- Inputs / outputs  
- Constraints  
- Out of scope  
- Unknowns / questions  
- Success criteria (testable)  
- Risks  
- Required human decisions (if any)  

## Clarification rules (SpecAgent)

- If intent is obvious, draft `spec.md` immediately.
- If ambiguous, ask up to **5** focused questions—do not interrogate endlessly.
- For high design risk, prefer structured Q&A but keep it bounded.

## Spec review

After `spec.md` is drafted, route reviews via [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `spec` → review agents `requirements`, `architecture` → **synthesis:** yes (see [review/SKILL.md](../review/SKILL.md)).

Detailed checklists live in `review/targets/spec.md` and `review/agents/*.md`; do not duplicate them here.

## Human spec gate (only standing human gate)

Before **plan**, the human completes understanding confirmation—not a trivia quiz—and records it:

- Copy [templates/human_spec_gate.md](../templates/human_spec_gate.md) to `.hermes/tasks/<task-id>/human_spec_gate.md` and fill it.

Full gate text and rationale: [human_gate.md](human_gate.md).

Do not enter **plan** until the human gate artifact exists and questions are resolved or explicitly accepted.

## Permissions

Spec agents: **no** product code edits, **no** test code edits. Artifacts only.
