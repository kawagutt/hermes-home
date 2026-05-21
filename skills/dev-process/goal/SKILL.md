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

## Stage-boundary model profile and usage (default)

**`current_stage` vs `--stage-id`:** `state.yaml` → `current_stage` is the orchestrator stage (`spec`, `plan`, `test`, `implementation`, `final`, …). **`--stage-id`** is the **usage stage id** (`stage_actions` key) for `artifacts.model_usage` rows and profile resolution when review, gates, or boundary recording need a different profile than `stage_defaults[current_stage]`. **Do not launch `dp_hermes.py` for review, gates, or boundary recording using only `current_stage`**—always pass the usage **`--stage-id`** (or the matching **`--action`**). With `current_stage=implementation` and no `--stage-id`, resolution uses `stage_defaults` → `dp-code`, which is wrong for checkpoint review.

| Work | `current_stage` | `--stage-id` at launch |
|------|-----------------|------------------------|
| spec draft | `spec` | omit → `dp-strong` via `stage_defaults` |
| spec review | `spec` | `spec_review` |
| implementation | `implementation` | `implementation` |
| checkpoint review (workers) | `implementation` | `--action review_*` (sessions in `review_manifest.yaml` only) |
| implementation phase (primary) | `implementation` | `implementation_phase_NN` |
| final review | `final` | `final_review` |

**Checkpoint reviews:** Review worker and synthesis sessions are recorded only in `reviews/implementation_phase_NN/round_MM/review_manifest.yaml`; do **not** add them to `artifacts.model_usage`. Primary implementation phase rows use `--stage-id implementation_phase_NN`. Final review uses `--stage-id final_review`. Reviewer launch details: [review/SKILL.md](../review/SKILL.md), [scripts/README.md](../scripts/README.md). With `current_stage=implementation`, **`dp_hermes.py` exits by default** if neither `--stage-id` nor `--action` is set (avoids silent `dp-code` resolution); use `--relaxed-launch` only when a warning is enough.

At **primary segment boundaries**, follow [validation/SKILL.md § Primary segment boundary completion](../validation/SKILL.md#primary-segment-boundary-completion) (canonical checklist). For **`standard`** / **`deep`**, a bounded `/goal` chain **must not** cross a primary segment boundary in one Hermes session (even when the profile is unchanged). **STOP** and restart with `dp_hermes.py --stage-id <next> --record-state -- chat`. When **`model_usage_required`** is **true** (or plan **`Model usage record required?`** is **yes**), do **not** advance the task/orchestrator to the **next primary segment** until the completed segment’s **`model_usage`** boundary row is recorded per that checklist (when the boundary maps to **`current_stage`**, do not update **`current_stage`** before the row exists—e.g. **`implementation_phase_NN`** usage rows while **`current_stage`** stays **`implementation`**). Role boundaries alone are not stops; primary segment boundaries are session stops. `handoff_required` / `session_reset_required` violations are caught by **`validate_model_governance.py --strict`** before final.

Safe deterministic helpers — no human confirmation. On helper failure, record `unknown` with reason and continue only until the next governance checkpoint; **`standard`** / **`deep`** tasks require **`validate_model_governance.py --strict`** before final.

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
