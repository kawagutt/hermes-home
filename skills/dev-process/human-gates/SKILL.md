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

## Gate approval recording

After the human gives an explicit gate decision, record it in **one coordinated pass** (procedural—validators do not parse gate artifacts).

**Approval decision** — update **both** in the same pass:

1. This gate’s **Approval** (and **Comments**, if any) in the gate artifact bound at `artifacts.human_spec_gate` or `artifacts.final_human_gate` (in-place on the current bound file; see [../artifacts/SKILL.md § Human gate artifacts](../artifacts/SKILL.md)).
2. Set the matching **`approved.human_spec_gate`** or **`approved.final_human_gate`** to `true` in `state.yaml`.
3. Clear **`pending_human_gate`** to `""`.
4. Run **`validate_state.py`** when appropriate.

**Reject / rework decision** — in the same pass:

1. Record the decision in the gate artifact **Approval** / **Comments** (in-place on the current bound file).
2. Keep the matching **`approved.*`** gate key **`false`**.
3. Clear **`pending_human_gate`** to `""`.
4. Reset the matching **`reviewed.*`** marker (`reviewed.spec` or `reviewed.final`) to **`false`**, record in timeline, and route rework per [../SKILL.md § Human gates](../SKILL.md#human-gates) (Task 1/2 rules—do not redefine here).
5. Run **`validate_state.py`** when appropriate.

## Pitfalls

- Do not collapse several required decisions into a single generic approval prompt.
- Do not treat an artifact that lists decisions as enough; the decisions must be presented in chat.
- Do not record approval before the human had a reasonable chance to respond to the individual items.
- Do not mix approval of implementation with approval to commit/push/merge unless the human explicitly confirms those actions.
- Do not switch from numbered choices to free-form-only prompts mid-sequence unless you first explain why.
- **`Required human decisions: None`:** means “no upstream itemized decisions,” **not** “human gate approval unnecessary.” Human gate approval is always required at spec/final gates.
- **Misleading “ready” phrasing:** e.g. `ready for the human-controlled` in a gate checklist implies work is done; **Proceed** / **`reviewed.*: true`** only means review passed—not gate approval.
- **Stale gate artifact:** the **current** gate file is only the one named in `state.yaml` → `artifacts.human_spec_gate` or `artifacts.final_human_gate`. Older `NNNN_*` files with the same stem are **history**—do not use them for gate decisions. On re-prompt, create a new numbered file, update the pointer, then set `pending_human_gate` (see [../artifacts/SKILL.md § Human gate artifacts](../artifacts/SKILL.md)). `## Superseded` on old files is optional; do not edit history files solely to add it—the pointer is authoritative either way.
- **Invisible choices:** Some UIs show “pick from the options above” without rendering options (e.g. narrow terminals). Always repeat **numbered options and decision titles in plain chat text** in the same message; duplicate AskQuestion options in the body ([`human_decision_prompt.md`](../templates/human_decision_prompt.md) § Visibility rule).

## References

When **`dev-process` is loaded**, treat **`dev-process` workflow + artifacts** as canonical; use **`../templates/human_decision_prompt.md`** (and **`../templates/human_spec_gate.md`** / **`../templates/final_human_gate.md`**) as the normative prompt shape for gated stages.

Otherwise, adopt the same one-decision-at-a-time chat pattern above; **`../templates/human_decision_prompt.md`** is a reusable stub.
