# Human spec gate

Task ID: `[YYYYMMDD_short-slug]` (e.g. `20260509_bounded-goal-dev-process`)  
Date: `[ISO date]`  
Human: `[name or handle]`

Before moving to **plan**, confirm understanding (not a quiz):

## Gate status

- `pending_human_gate`: `human_spec_gate` (set in `state.yaml` before gate choices in chat)
- `gate_prompted_at`: `[ISO timestamp from state.yaml]`
- `reviewed.spec: true` / spec synthesis **Proceed** does **not** mean spec gate approval (`approved.human_spec_gate` may still be `false`).
- The agent must present **numbered approval choices in chat** before waiting for a human response.

## 1. Goal

State the task’s purpose in **one sentence**:

> 

## 2. Non-goal

Name **one** explicit non-goal you will not pursue in this round:

> 

## 3. Success criteria

What measurable or verifiable outcomes mean **done**?

> 

## 4. Main risk

What is the **highest-risk** failure mode, and where is it captured in **`artifacts.spec`** (see `state.yaml`)?

> 

## Required human decisions

This section refers to **itemized decisions from upstream** (e.g. in **`artifacts.spec`**)—not to whether the human spec gate itself is required.

**Do not** list `None` alone under **Required human decisions** (often read as “spec gate approval not needed”). When there are no upstream itemized decisions for this round, use:

- **Itemized decisions from upstream:** none recorded in spec/summary for this gate round.
- **Spec gate approval:** still required before **plan** (see § 5. Approval).

Use the chat structure in [human_decision_prompt.md](human_decision_prompt.md) when presenting items (adapt the final approval line to “proceed to **plan**” for this gate). Follow **§ Visibility rule** there: each decision needs a **clear title** (what is being decided) and **numbered options repeated in plain chat text** in the same message—do not rely on UI-only choice lists.

If **`artifacts.spec`** contains `Required human decisions`, present those items **one by one in chat** before asking for **approval to proceed to plan**. For each item, record the decision question, recommendation, practical consequences, whether it blocks plan, and the artifact section to update. The gate artifact records the discussion; it is not a substitute for the discussion.

## Short CUI approval

Before asking for approval, provide a concise Japanese summary at **`artifacts.spec_summary_ja`** (path from `state.yaml`). A short response such as `OK` is acceptable only after the summary and after required decision items have been presented individually with an opportunity for the human to answer or discuss them. Do not collapse multiple required human decisions into a single generic `OK` prompt. Record the exact response and any comments here. If comments require material changes to **`artifacts.spec`**, update it, rerun required spec review if material, provide an updated Japanese summary, and ask for confirmation again before plan.

## 5. Approval

- [ ] I approve proceeding to **plan** with the current **`artifacts.spec`**.  
- [ ] Residual questions (if any) are listed below and accepted for planning.

**Residual questions / decisions**

> 
