---
name: dev-process-goal
description: >-
  Hermes `/goal` continuation rules: legal stage chaining, explicit role transitions,
  operational stops and stop-report format. Use when continuing dev-process beyond a single phase
  or handing off roles without invoking a human gate.
---

# `/goal` and continuation (`dev-process`)

Human gate approval rules live in [../SKILL.md](../SKILL.md#human-gates). This file covers ordinary `/goal` operation.

## Bounded `/goal` operating contract

A short request such as `Start a new task. Goal: ...` is enough to begin a dev-process task. If the user does not provide a task id, **generate** one in the form **`YYYYMMDD_<short-slug>`** (8-digit date, underscore, slug—for example `20260509_bounded-goal-dev-process`). **Do not** generate the legacy `<slug>-YYYYMMDD` / `<slug>_YYYYMMDD` trailing-date shape **by default**. If the human **explicitly** provides a different task id, **use it as given** unless it conflicts with safety, repository policy, or filesystem constraints. Create `.hermes/tasks/<task-id>/`, initialize `state.yaml` from [templates/state.yaml](../templates/state.yaml), and start at `spec`. When materializing or versioning task-root Markdown, follow [artifacts/SKILL.md — Numbered task-root artifacts](../artifacts/SKILL.md#numbered-task-root-artifacts); append **`artifacts.timeline`** in the same session when recording branch or other process events. Before asking for the spec human gate, check whether dev-process **can create** a dedicated branch for this task (or the human must explicitly direct branch choice) and record branch feasibility in the spec summary or gate artifact (see [git/SKILL.md](../git/SKILL.md)).

When continuing an existing task, read `.hermes/tasks/<task-id>/state.yaml` first. Resume from `current_stage`, `current_phase`, `review_rounds`, `latest_reviews`, and **`pending_human_gate`**; do not rely on chat history alone. If `pending_human_gate` is non-empty, treat the task as waiting at that gate regardless of `current_stage`.

**Hermes-compatible hint:** Use **one main model tier per Hermes session**, switching **Hermes profiles** (`dp-strong`, `dp-review`, `dp-code`, `dp-cheap`) at stage boundaries when the next role needs a different tier. **Reasoning effort follows the chosen review-depth preset** (`light` → no high by default; `standard` → medium until escalated; `deep` → high reasoning effort for syntheses, ambiguous triage, impact/architecture, final recommendation). See [validation/SKILL.md — Reasoning effort by review-depth preset](../validation/SKILL.md#reasoning-effort-by-review-depth-preset) and **`artifacts.plan`** preset lines.

When the approved plan is written, set **`state.yaml` → `review_depth_preset`** to `light`, `standard`, or `deep` (must match the plan). If omitted, helpers infer it from **`artifacts.plan`** when possible.

## v4 (new tasks)

**`1 /goal = 1 job` only** — then STOP. Full contract: [validation/SKILL.md § v4 Job Contract](../validation/SKILL.md#v4-job-contract-canonical--new-tasks-only).

```text
run-dp job start --role <role> [--handoff-in path ...]
  → new Hermes session
  → work
  → write handoff_out
run-dp job close --session-export ...
run-dp validate --strict   # before final_human_gate numbered approval
```

Session/model evidence: `jobs.yaml` only. Display: `run-dp render model-usage|review-summary`.

## Pre-v4 only (tasks without jobs.yaml)

**`current_stage` vs `--stage-id`:** orchestrator stage vs usage stage id for `model_usage` / `dp_hermes.py`. Do not launch review using only `current_stage=implementation` (resolves to `dp-code`).

| Work | `current_stage` | Launch |
|------|-----------------|--------|
| spec draft | `spec` | `dp_hermes.py` (stage default) |
| spec review | `spec` | `--stage-id spec_review` or `review_*` |
| implementation phase | `implementation` | `--stage-id implementation_phase_NN` |
| checkpoint review | `implementation` | `--action review_*` → `review_manifest.yaml` |
| final review | `final` | `--stage-id final_review` |

Primary boundaries: [validation/SKILL.md](../validation/SKILL.md) (legacy sections) + `dp_stage_boundary.py`. Governance: `validate_model_governance.py --strict`. **Do not mix** with v4 `run-dp` on the same task.

## Human gate invariants (/goal STOP)

```text
reviewed.final == true does not imply approved.final_human_gate == true.

pending_human_gate != "" means the orchestrator must stop,
even if latest review recommendation is Proceed.
```

```text
reviewed.spec == true does not imply approved.human_spec_gate == true.
```

**Plan must not start until:**

```text
reviewed.spec == true
approved.human_spec_gate == true
pending_human_gate == ""
```

Do not use `approved.spec` (legacy / non-canonical if present in older task state).

If **`pending_human_gate`** is non-empty, **STOP** immediately—even when the latest review synthesis recommends **Proceed** or `reviewed.final` / `reviewed.spec` is already `true`. Do not advance to the next stage until the human completes the gate (approve or reject/rework) and **`pending_human_gate`** is cleared. See [../SKILL.md § Human gates](../SKILL.md#human-gates) for gate presenter order and post-decision state updates.

## Legal continuation vs required stops

`/goal` may continue across ordinary stage or phase boundaries when the next action is legally allowed by `state.yaml`, gate approvals, required artifacts, latest review synthesis, role permissions, and the approved plan. Do **not** continue while **`pending_human_gate`** is non-empty. Do **not** stop merely because a phase completed if the next stage is legal and the same agent/session may perform it.

A bounded advancement may be one stage, one implementation phase, one review target plus selected agents, one synthesis/status step, or a **short** legal chain of those steps until a required stop condition is reached. **Role boundary is not an automatic stop condition.** Do not stop solely because the next legal action belongs to another role.

When the next legal action requires a different role (for example PlanAgent → TestAuthorAgent → ImplementationAgent → ReviewerAgent), continue with an **explicit role transition** when the next action is legal under `state.yaml`, approvals, latest review synthesis, role permissions, and the approved plan. An explicit role transition names the new role and allowed scope; it is not a human gate. Stop with a handoff report only when continuing would be unsafe or illegal, the next role requires unavailable context/tools, or a required gate/escalation decision is pending. Do not silently change role inside the same `/goal` loop, but also do not stop solely because the next legal action belongs to another role. Normal role/stage transitions **do not require human confirmation** merely because the next action belongs to another dev-process role. Human confirmation is required only at hard human gates or when escalation, scope, safety, branch, or policy decisions require it.

Explicit role transition must not weaken review context isolation. Reviewer roles should receive approved artifacts, diffs, test outputs, and prior review summaries as needed, but not ImplementationAgent chat rationale unless explicitly requested. In particular, ImplementationAgent → ReviewerAgent transitions should preserve independent review context instead of reusing implementation rationale as review evidence.

## Operational stops

**Human gate wait:** if **`pending_human_gate`** is non-empty, STOP (required; not optional). Include `pending_human_gate`, `gate_prompted_at`, and the gate artifact path in the stop report.

Outside hard human gates, stop only when continuing would be unsafe or illegal, including:

- blocking review synthesis or unresolved escalation;
- next required action belongs to a different role **and** continuing by explicit role transition would be unsafe, illegal, or missing required context/tools;
- required artifacts are missing or inconsistent;
- continuing would change scope, public behavior, role permissions, artifact policy, branch/commit policy, or validation policy;
- the agent is uncertain which stage is legally next.

When stopping, write a short stop report:

```text
Stopped because:
What I need from the human:
Next allowed action after resolution:
Relevant artifacts: (include pending_human_gate / gate_prompted_at when a human gate wait is active)
```

Do not stop with only “phase complete” or “waiting for next instruction” unless a human gate or blocker actually requires it.

This section documents process behavior for Hermes `/goal`; it does not implement or require Hermes CLI, gateway, slash-command, agent-loop, or executable model-routing changes.
