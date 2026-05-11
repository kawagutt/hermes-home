---
name: dev-process-human-gates
description: >-
  Companion to dev-process for human approval gates: decision-item prompting, artifact-vs-chat
  boundaries, approval evidence. Load with dev-process when a workflow has hard human gates before
  planning, merge, completion, or other irreversible transitions; dev-process stays canonical.
---

# Human gates (dev-process companion)

This companion **does not** define dev-process gate policy by itself. When **dev-process** is loaded, the canonical rule is [`SKILL.md` § Human gates](../SKILL.md#human-gates). This file only gives reusable prompting discipline and examples ([`human_decision_prompt.md`](../templates/human_decision_prompt.md), [`human_spec_gate.md`](../templates/human_spec_gate.md), [`final_human_gate.md`](../templates/final_human_gate.md)).

Use when operating a staged process that includes human approval gates—for example before planning, final completion, merge, release, scope changes, public behavior changes, or branch/commit-policy changes.

## Core rule

A human gate is not satisfied merely because an artifact exists or because a summary was written. The human must receive the required decisions in chat with a chance to answer or discuss them.

Canonical question format (must stay stable unless a workflow explicitly overrides it):

1. Ask with visible **numbered choices** (`1.`, `2.`, `3.`) whenever practical.
2. Do **not** post a long paragraph/list and then ask only a generic `OK?`.
3. Before waiting, explicitly state **how to answer** (e.g. `Reply with 1/2/3 or a short comment.`).
4. Do **not** change the question format mid-gate without a clear reason announced in chat.

If the gate has multiple required decisions:

1. Present the concise decision summary first, in the workflow's required language and format.
2. Present each required human decision as an individually answerable item (for each: decision question; recommended answer, if any; practical consequence of each option; whether it blocks the next stage; artifact section to update).
3. Give the human a chance to answer or discuss each item.
4. Only after that, a short confirmation such as `OK` may be accepted as approval.
5. Record the approval and comments in the gate artifact or workflow log.

## Artifact-vs-chat boundary

Gate artifacts are evidence and working logs. They do **not** replace the chat interaction.

Do not say or imply that a generic `OK` is sufficient when the individual required decisions have not yet been surfaced in chat.

## Common gate decision categories

At a final development gate, consider prompting separately for:

- approval of the implementation/result;
- whether to commit, push, merge, or leave changes uncommitted;
- whether working-log artifacts are excluded from commits;
- handling of project-level docs or specs;
- acceptance of follow-up work as out of scope.

At a spec gate, consider prompting separately for:

- goal and non-goal agreement;
- success criteria agreement;
- unresolved risks or assumptions;
- branch or task-scope decisions;
- any explicit human decisions listed in the spec summary.

## Pitfalls

- Do not collapse several required decisions into a single generic approval prompt.
- Do not treat an artifact that lists decisions as enough; the decisions must be presented in chat.
- Do not record approval before the human had a reasonable chance to respond to the individual items.
- Do not mix approval of implementation with approval to commit/push/merge unless the human explicitly confirms those actions.
- Do not switch from numbered choices to free-form-only prompts mid-sequence unless you first explain why.
- **Invisible choices:** Some UIs show “pick from the options above” without rendering options (e.g. narrow terminals). Always repeat **numbered options and decision titles in plain chat text** in the same message; duplicate AskQuestion options in the body ([`human_decision_prompt.md`](../templates/human_decision_prompt.md) § Visibility rule).

## References

When **`dev-process` is loaded**, treat **`dev-process` workflow + artifacts** as canonical; use **`../templates/human_decision_prompt.md`** (and **`../templates/human_spec_gate.md`** / **`../templates/final_human_gate.md`**) as the normative prompt shape for gated stages.

Otherwise, adopt the same one-decision-at-a-time chat pattern above; **`../templates/human_decision_prompt.md`** is a reusable stub.
