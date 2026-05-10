# Review-depth preset selection

Review depth is selected by **remaining uncertainty** and **impact if broken**, not by diff size alone.

First run deterministic checks where possible. Do not spend high-reasoning review budget on facts that commands can verify. Then choose the smallest preset that still covers the remaining risk.

## Selection rule

```text
if any high-risk answer is yes:
  deep

else if deterministic checks cover most risk
and no externally observable product behavior/API/CLI/data-contract or architecture risk
and rollback is easy:
  light

else:
  standard
```

A smaller diff does not automatically mean `light`. A large but mechanical docs update may be `light`; a one-line security or API change may be `deep`.

Documentation text-only changes do not count as externally observable product behavior/API/CLI/data-contract triggers by themselves, unless they change promised behavior, user-facing policy, contract semantics, or operational instructions that users rely on.

Human preference for a lighter preset does not override high-risk triggers. If a high-risk trigger is present, escalate to `deep` or stop for an explicit scope/risk decision.

## Reasoning effort (Hermes-compatible runtimes)

**Bind reasoning effort to the selected preset.** Authoritative table and guardrails: [validation/SKILL.md — Reasoning effort by review-depth preset](../validation/SKILL.md#reasoning-effort-by-review-depth-preset).

Summary:

```text
light   → default/medium reasoning; never high by default; escalate preset if risk grows
standard → default/medium; move to deep (then high) when triggers appear
deep    → high for synthesis, ambiguous blocker triage, architecture/impact, final recommendation
```

`deep` / high aligns with **this file’s selection rule**: externally observable behavior/API/CLI/contracts, architecture, migration/schema, security/privacy, unresolved human decisions, hard rollback, low test confidence. See the `deep` row below.

Ordinary **`standard`** work stays medium until escalation; **preset upgrade precedes flipping reasoning to high**.

## Canonical preset definitions

This file is the **single source of truth** for preset reviewer requirements and preset synthesis rules. Other docs may summarize or link to it, but must not define competing reviewer lists or synthesis rules.

| Preset | Meaning / when to use | Required reviewers | Synthesis rule | Deterministic checks | Escalation triggers |
|--------|------------------------|--------------------|----------------|----------------------|---------------------|
| `light` / `fast` | Mostly mechanical or docs/template work where deterministic checks cover most risk, rollback is easy, and there are no behavior/API/architecture/security/persistence concerns or unresolved blocking human decisions. | Required: `checklist_compliance`. Optional when relevant: `naming_doc`, `requirements`. | Required before any gate or stage advancement when there is any blocking/potential-blocking finding, reviewer disagreement, unresolved question, or human decision. For purely mechanical low-risk checkpoint reviews with clean deterministic checks and no findings, synthesis may be a compact Orchestrator summary recorded in the timeline or review notes. Final review still requires compact synthesis before `final_human_gate`. | Artifact/state checks, syntax checks, content/path checks, targeted validations, helper validation, review-round consistency. | Any high-risk trigger, uncertain requirements mapping, contested validation waiver, missing gate/branch/artifact evidence, possible blocker, reviewer disagreement, or unresolved human decision. |
| `standard` | Default for normal scoped changes that are not clearly `light` and have no `deep` trigger; requires local correctness, requirements alignment, or test-quality judgment. | Required baseline: `checklist_compliance` plus one or both of `requirements` and `diff_detail`, selected by target. Required: `test_quality` when tests change or validation confidence matters. Add `architecture` or `impact` when their uncertainty exists, or escalate to `deep` if those risks are high. | Required for plan/test/final and whenever blocking/potential-blocking findings, reviewer disagreement, unresolved questions, or escalation triggers appear. For implementation checkpoints, synthesis is required unless the plan explicitly marks the checkpoint as low-risk and all required reviewers are clean. | All light checks plus targeted tests, lint/type checks, validation command capture, checklist coverage summaries. | High-risk trigger discovered; broad impact; low test confidence; repeated failures; unresolved reviewer disagreement; ambiguous algorithm/edge-case correctness. |
| `deep` / `high-risk` | Any high-risk trigger: externally observable product behavior, API, CLI, or data-contract change; architecture/boundary change; security/permission/secrets/privacy; persistence/schema/migration/serialization; broad/cross-module refactor; hard rollback; low test confidence; impact outside edited files; important unresolved human decision. | Required: `requirements`, `architecture`, `diff_detail`, `impact`, `test_quality`. Optional/additional when relevant: `naming_doc`, `security/privacy`, `performance`, domain/algorithm reviewer. | Required. Blocking triage must be explicit and assigned to an owner. Synthesis is the merge step for reviewer outputs, not another independent reviewer agent. | All standard checks; helpers gather evidence but do not replace high-reasoning review, domain review, or empirical validation. | Already high-risk; escalate further to human/domain specialist when uncertainty remains after deep review. |

## Optional specialist reviewers

Optional specialist reviewers are added when the selected preset leaves domain-specific uncertainty that the required reviewers do not cover. Examples include `security/privacy`, `performance`, domain/algorithm, data migration, accessibility, or product-policy reviewers.

Optional specialist reviewers do **not** lower the preset, replace required reviewers, or replace synthesis. If a specialist reviewer finds a blocking or potential-blocking issue, the synthesis step must triage it to an owner just like any other reviewer finding.
