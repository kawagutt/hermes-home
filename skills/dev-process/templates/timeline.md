# Timeline

Append-only log: **when** each stage ran, **what happened**, **which artifacts** were produced.

Add a new row **after each meaningful step** (draft, review round, gate, rework, rerun). Never delete or rewrite earlier rows except to fix typos noted in a follow-up row.

| Time | Stage | Action | Output |
|------|-------|--------|--------|
| | spec | Drafted spec | `spec.md` |
| | spec review | Ran requirements + architecture review | `reviews/spec/round_01/synthesis.md` |
| | human gate | Approved spec | `human_spec_gate.md` |
| | plan | Drafted plan | `plan.md`, `phase_checklists.md` |

Use ISO-like timestamps in local or UTC consistently (e.g. `2026-05-09 21:30`).

When recording rework and reruns, follow **Review rounds and rework history** in `skills/dev-process/review/SKILL.md`.
