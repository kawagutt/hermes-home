---
name: dev-process-spec
description: >-
  Produces the task spec artifact from goals, non-goals, success criteria, risks, and constraints; runs spec
  review via review router; captures human_spec_gate before plan. Use when authoring or
  revising specification for a Hermes dev-process task after loading dev-process.
---

# Spec stage

Produce and stabilize **what** to build before any implementation or test code work.

## Outputs

Primary artifact: `.hermes/tasks/<task-id>/` + **`artifacts.spec`** (**working spec** for this task; task-root filenames follow [artifacts/SKILL.md — Numbered task-root artifacts](../artifacts/SKILL.md#numbered-task-root-artifacts); persistence and promotion: [artifacts/SKILL.md — Artifact persistence policy](../artifacts/SKILL.md#artifact-persistence-policy)).
Start from [templates/spec.md](../templates/spec.md).

After spec reviewer agents finish for this run, write outputs under `.hermes/tasks/<task-id>/reviews/spec/round_NN/` (see [artifacts/SKILL.md — Review outputs by stage](../artifacts/SKILL.md#review-outputs-by-stage)): per-agent files such as **`requirements.md`**, **`architecture.md`**, plus **`synthesis.md`** (unprefixed names under `reviews/`).

## Required content in the spec artifact (`artifacts.spec`; path from `state.yaml`)

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

- If intent is obvious, draft **`artifacts.spec`** immediately.
- If ambiguous, ask up to **5** focused questions—do not interrogate endlessly.
- For high design risk, prefer structured Q&A but keep it bounded.

## Spec review

After **`artifacts.spec`** is drafted, route reviews via [review/SKILL.md](../review/SKILL.md).

**Standard recipe:** target `spec` → review agents `requirements`, `architecture` → **synthesis:** yes (see [review/SKILL.md](../review/SKILL.md)).

Detailed checklists live in `review/targets/spec.md` and `review/agents/*.md`; do not duplicate them here.

## Human spec gate

Before **plan**, the human completes understanding confirmation—not a trivia quiz—and records it:

- Write or update a concise Japanese decision summary at **`artifacts.spec_summary_ja`** (task-root filename per [artifacts/SKILL.md — Numbered task-root artifacts](../artifacts/SKILL.md#numbered-task-root-artifacts)) covering goal, non-goals, success criteria, risks, and required human decisions.
- Copy [templates/human_spec_gate.md](../templates/human_spec_gate.md) to `.hermes/tasks/<task-id>/` + **`artifacts.human_spec_gate`** (task-root filename per [artifacts/SKILL.md — Numbered task-root artifacts](../artifacts/SKILL.md#numbered-task-root-artifacts)) and fill it.
- A short CUI approval such as `OK` is valid only after the Japanese summary at **`artifacts.spec_summary_ja`** and after any `Required human decisions` have been presented **one by one in chat** (see [../SKILL.md](../SKILL.md#human-gates)); record the response and comments in **`artifacts.human_spec_gate`**.

Full gate text and rationale: [human_gate.md](human_gate.md). Shared gate/summary rules: [../SKILL.md](../SKILL.md#human-gates).

Do not enter **plan** until the human gate artifact exists and questions are resolved or explicitly accepted. If human-gate feedback causes material changes to **`artifacts.spec`**, apply [artifacts/SKILL.md — Numbered task-root artifacts](../artifacts/SKILL.md#numbered-task-root-artifacts) (edit in place when this file is the highest-numbered task-root artifact; otherwise create a new `NNNN_spec.md` and repoint `artifacts.spec`), rerun required spec review if material, provide an updated Japanese summary, and ask for confirmation again before planning.

## Permissions

Spec agents: **no** product code edits, **no** test code edits. Artifacts only.
