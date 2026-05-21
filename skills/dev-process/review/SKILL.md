---
name: dev-process-review
description: >-
  Routes independent reviews by combining a target (what to review) with agents (perspective) and
  shared output templates. Defines blocking vs non-blocking findings and synthesis rules. Does not
  contain per-reviewer checklists—those live in targets/ and agents/. Use when assigning reviews in
  dev-process.
---

# Review process (router)

## Reviewer launch checklist

Before starting a review round:

- Use approved artifacts, concise diffs, test outputs, and prior review summaries only.
- Do **not** pass ImplementationAgent chat logs or rationale unless the human explicitly requests them.
- Confirm `state.yaml` / latest synthesis / gate approvals match the review target.
- Launch Hermes with the correct usage **`--stage-id`** (or **`--action review_*`**) per [goal/SKILL.md](../goal/SKILL.md)—**never** rely on `current_stage=implementation` alone (that resolves to `dp-code`). Use `dp_hermes.py --strict-launch` or `DEV_PROCESS_STRICT_LAUNCH=1` to fail fast when `--stage-id` is omitted.

## Review worker sessions (MUST)

Each **required reviewer perspective** runs in a **separate Hermes session** unless the human explicitly waives this in the task record.

- Do **not** run multiple reviewer perspectives in one shared session.
- **Synthesis** runs in a **separate session** from every individual reviewer job.
- Resolve each worker with [`dp_review_job.py`](../scripts/dp_review_job.py), then launch `dp_hermes.py --action review_<agent> -- chat` **without** `--record-state`. After each session, record evidence via `dp_review_job.py --record-session` (see [scripts/README.md](../scripts/README.md) § `dp_review_job.py`).
- Review sessions live in **`reviews/<stage>/round_NN/review_manifest.yaml`** only.
- **`artifacts.model_usage`** records **primary** loop boundaries only—do **not** duplicate reviewer worker rows there.

Preset reviewer lists: [presets.md](presets.md) (source of truth); machine mirror: [`config/review_targets.yaml`](../config/review_targets.yaml).

Reviews combine:

1. A **target** from [`targets/`](targets/) — defines *what* is in scope.  
2. One or more **independent review agents** (prompts under [`agents/`](agents/) *except* [`synthesis.md`](agents/synthesis.md)) — *how* to look at the target from each perspective.  
3. Shared **output format** per reviewer via [`templates/review_result.md`](templates/review_result.md).  

After reviewers finish, optionally run a **synthesis role** ([`agents/synthesis.md`](agents/synthesis.md)) that merges their outputs using [`templates/synthesis_result.md`](templates/synthesis_result.md) → **`synthesis.md`**. **Synthesis is not another independent reviewer agent**—it aggregates reviewer outputs without inventing new primary findings.

`review/targets/*.md` and `review/agents/*.md` are **reference prompt fragments**, not standalone skills. This file is the **router** only: **recipes + contract**, not detailed checklists.

## Cheap-checker escalation

Cheap/medium reviewers may flag possible blockers during mechanical or routine checks, but final blocker decisions belong to synthesis or a higher-reasoning reviewer. Do not let a cheap checker alone make irreversible advancement or merge decisions.

## Findings classification

Each reviewer labels items as one of:

- **blocking** — must fix or re-scope before advancing.  
- **non-blocking** — should fix soon; documented technical debt acceptable with rationale.  
- **question** — needs author or human clarification.  
- **suggested follow-up** — optional improvement.  

## Context isolation

- Do not attach ImplementationAgent conversational rationale unless explicitly requested.  
- Prefer approved artifacts, concise diffs, test outputs, and prior review summaries.  

## Synthesis

A **synthesis** step merges independent reviewer files into one recommendation (`synthesis.md`) using [`templates/synthesis_result.md`](templates/synthesis_result.md). It should resolve duplicated findings and state **merge/readiness**.

Synthesis **per implementation phase** may be skipped for cost; final synthesis should not be skipped arbitrarily when merge decisions matter. Final review synthesis precedes `final_human_gate`; after final synthesis and validation evidence, provide a concise Japanese final summary and record the human decision in **`artifacts.final_human_gate`** (path from `state.yaml`).

---

## Rework routing

After review, the round’s **`synthesis.md`** must drive **finding triage** for every **blocking** item. Do **not** default to “send everything to ImplementationAgent.”

Base loop:

```text
review NG → synthesis classifies blocking findings → fix in owning stage → run tests → rerun required review(s)
```

**Synthesis must assign each blocking finding to exactly one rework owner** (MUST in `synthesis.md` when recommendation is not **Proceed**):

- `implementation` — product code fix (bugs, checklist gaps inside plan, edge cases, diff-detail issues).  
- `test` — test code/spec alignment, brittleness, wrong assertions/fixtures; **not** patched by ImplementationAgent.  
- `plan` — plan wrong or superseded → PlanAgent → plan review → possibly test updates → implementation resumes.  
- `spec` — spec wrong or ambiguous → SpecAgent → spec review → **human spec gate** if materially changed → re-execute plan and later stages as needed.  
- `artifact` — numbered task-root artifact repair only (`artifacts.*`, timeline, gates) without product code changes.  
- `human` — decision or policy required before any agent edits.

**Blocking handoff columns (MUST):** for every blocking row in [`templates/synthesis_result.md`](templates/synthesis_result.md): **Owner**, **Exact file/section**, **Required action**, **Re-review required** (`yes — <stage> review` or `no`). Vague “fix needed” without location and next step is non-compliant; `review_round.py --finish` rejects incomplete synthesis.

Output must be **actionable** for the **next session** — the owner stage should not re-litigate the same finding without new evidence.

Cross-reference: [implementation/SKILL.md](../implementation/SKILL.md) (rework after review, test failure triage).

---

## Review rounds and rework history

Do **not** overwrite a previous review result. Each full review cycle for a stage gets its own subdirectory:

```text
.hermes/tasks/<task-id>/reviews/<stage>/round_NN/
```

Stages use the orchestrator naming: `spec`, `plan`, `test`, `implementation_phase_<NN>`, `final`.

When **blocking** findings cause rework:

1. Record the finding chain in **`artifacts.rework_log`** ([template](../templates/rework_log.md); path from `state.yaml`).  
2. Assign each blocking item’s **owner** in **`synthesis.md`** (rework routing above).  
3. Fix work in the **owning** stage (`spec`, `plan`, `test`, or implementation).  
4. **Append** a row to **`artifacts.timeline`** ([template](../templates/timeline.md); path from `state.yaml`).  
5. Run the required **tests**.  
6. **Re‑run** the relevant review(s) into the **next** `round_NN` directory; **synthesis** (or Orchestrator if synthesis skipped) updates `review_rounds` / `latest_reviews` ([Who updates `state.yaml`](#who-updates-stateyaml)).  

Same pattern applies whether the finding came from checkpoint review or final review: preserve prior rounds so the task-local **“review → fix → re‑review”** chain stays traceable (**not** project Git history—the task tree is normally uncommitted working log—see [artifacts/SKILL.md — Artifact persistence policy](../artifacts/SKILL.md#artifact-persistence-policy)).

### Who updates `state.yaml`

**Routine (default):**

- **`review_rounds.<stage>`** and **`latest_reviews.<stage>`** are maintained by whichever agent/session performs the **synthesis** step for that review round—that is the **synthesis role** described in [`agents/synthesis.md`](agents/synthesis.md).
- Timing: **immediately after** successfully writing **`reviews/<stage>/round_NN/synthesis.md`**, bump the counter for `<stage>` to `NN` (integer matching the round suffix) and set `latest_reviews.<stage>` to that file’s repo-relative task path.
- **`reviewed.*` (review-pass only):** synthesis sets the matching **`reviewed.<key>: true`** only when the recommendation **accepts** the stage (e.g. **Proceed**). Rework or blocking synthesis must **not** set `reviewed.*` to `true`. Use only keys defined in [templates/state.yaml](../templates/state.yaml): `spec`, `plan`, `tests`, `final` — mapping: `spec` → `reviewed.spec`; `plan` → `reviewed.plan`; `test` → `reviewed.tests`; `final` / `final_diff` → `reviewed.final`; **`implementation_phase`** checkpoints → do **not** update `reviewed.*` (only `review_rounds` / `latest_reviews` for that phase key).
- Synthesis must **not** set **`approved.*`**, **`pending_human_gate`**, or **`gate_prompted_at`**.

**Gate presenter (Orchestrator or coordinating agent):** after a human gate stage is ready (e.g. spec/final review Proceed), before numbered gate choices in chat: (1) gate artifact ready, (2) `pending_human_gate` + `gate_prompted_at`, (3) timeline `gate_prompted`, (4) chat prompt, (5) STOP. See [../SKILL.md § Human gates](../SKILL.md#human-gates).

**Humans (or orchestrator recording human choice):** after **any** explicit gate decision (approve or not approved / rework), clear **`pending_human_gate`**. If approved, set the matching canonical gate key: **`approved.human_spec_gate`** or **`approved.final_human_gate`**. If not approved, keep the matching canonical gate key **false**, record in gate artifact / timeline, set **`current_stage`** to the rework route.

**Humans:** not required for `review_rounds` / `latest_reviews` / `reviewed.*` in normal agent workflows. Humans may patch `state.yaml` only when recovering from tooling failure or operating **without** a synthesis agent—in that case, treat it as orchestration hygiene with a note in **`artifacts.timeline`**.

**If synthesis was skipped** for that round (allowed only where the router marks synthesis **optional**):

- The **Orchestrator** (coordinating agent/session) MUST still update `review_rounds` / `latest_reviews` consistently with where reviewer outputs landed, OR delegate an explicit follower step to combine reviewers first. Apply the same **Proceed-only** rule if setting `reviewed.*`.

**Independent reviewers must not each bump `review_rounds`**—only synthesis (or orchestrator fallback) avoids races and partial rounds.

---

## Standard target recipes (combinations only)

These are default **target recipes** for the `standard` preset. The single source of truth for preset reviewer requirements and synthesis rules is [`presets.md`](presets.md). For `light` or `deep`, use [`presets.md`](presets.md). Do not treat this section as overriding the selected review-depth preset.

Recipes name **targets** and common standard **review agents** only. **Synthesis** is a separate line (merge step). **Detailed bullets stay in agent files.**

### Spec review

- **target:** `spec` (`targets/spec.md`)  
- **review agents:** `requirements`, `architecture`  
- **synthesis:** yes  

### Plan review

- **target:** `plan` (`targets/plan.md`)  
- **review agents:** `architecture`, `checklist_compliance`, `impact`  
- **synthesis:** yes  

### Test review

- **target:** `test` (`targets/test.md`)  
- **review agents:** `requirements`, `test_quality`, `checklist_compliance`  
- **synthesis:** yes  

### Implementation phase checkpoint

- **target:** `implementation_phase` (`targets/implementation_phase.md`)  
- **review agents:** `checklist_compliance`, `diff_detail`, `architecture`  
- **synthesis:** optional (skip for cheap phases if team policy allows)  

### Final review

- **target:** `final_diff` (`targets/final_diff.md`)  
- **review agents:** `architecture`, `diff_detail`, `impact`, `naming_doc`, `test_quality`  
- **synthesis:** required  
- **after synthesis (Proceed):** set **`reviewed.final: true`**, write/refresh **`artifacts.final_summary_ja`**, then gate presenter runs final gate order (pending state → timeline → chat → STOP) at **`final_human_gate`**  

---

## Task output locations

Write reviewer and synthesis artifacts under `.hermes/tasks/<task-id>/reviews/<stage>/round_NN/` per [`artifacts/SKILL.md`](../artifacts/SKILL.md). Each new review run increments the round folder; keep **`artifacts.timeline`** / **`artifacts.rework_log`** in sync.

### Filenames inside each `round_NN`

Use **conventional unprefixed names** (e.g. `requirements.md`, `architecture.md`, `synthesis.md`) per agent role and [`templates/review_result.md`](templates/review_result.md) / [`templates/synthesis_result.md`](templates/synthesis_result.md). **Do not** use `NNNN_` prefixes under `reviews/`—those apply only to **task-root** artifacts ([`artifacts/SKILL.md`](../artifacts/SKILL.md) § Numbered task-root artifacts).

## Task completion tail

After implementation validation: run checkpoint + **final** review (`reviews/final/round_NN/`). On **Proceed**, synthesis sets **`reviewed.final: true`**. Materialize **`artifacts.final_summary_ja`** and **`artifacts.final_human_gate`**. Gate presenter: set **`pending_human_gate: final_human_gate`** and **`gate_prompted_at`** (and timeline) **before** numbered final-gate options in chat, then STOP. After explicit human decision: clear **`pending_human_gate`**; on approval set **`approved.final_human_gate: true`**, on reject/rework keep it `false` and route rework; re-run `validate_state.py` when appropriate. **Do not** auto-commit, merge, or push; final gate approval is not a git operation.
