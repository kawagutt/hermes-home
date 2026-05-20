# Synthesis template

Written as **`synthesis.md`** inside **`.hermes/tasks/<task-id>/reviews/<stage>/round_NN/`** — one round per review run (**never overwrite** previous `round_*` dirs). **Do not** use `NNNN_` prefixes under `reviews/` (task-root only; see [`artifacts/SKILL.md`](../../artifacts/SKILL.md#numbered-task-root-artifacts) § Numbered task-root artifacts).

## Meta

- Task ID: `[YYYYMMDD_short-slug]`  
- Stage: `[spec | plan | test | implementation_phase_NN | final]`  
- Review round: `[round_01]` — must match subdirectory name.  
- Date: `[ISO date]`  

## Recommendation

Pick **exactly one** primary (one `- [x]`):

- [ ] Proceed  
- [ ] Rework tests  
- [ ] Rework plan  
- [ ] Rework implementation  
- [ ] Stop — human decision required  

**One-line rationale:**

[Sentence]

## Rework owner (blocking findings)

**Required when** the recommendation is anything other than **Proceed** (rework / stop). For each **blocking** finding from reviewers, fill **one row** — do not default every item to `implementation`.

| ID source | Summary | Owner | Exact file/section | Required action | Re-review required |
|-----------|---------|-------|--------------------|-----------------|------------------|
| e.g. F1 architecture | One-line finding | spec / plan / test / implementation / artifact / human | `path:line` or `artifacts.plan` §… | Concrete edit or command | yes — plan review |
| | | | | | |

**Owner values (exactly one per row):** `spec`, `plan`, `test`, `implementation`, `artifact` (task-root artifact repair only), or `human` — do not write slash-separated lists.

**Re-review required:** `yes — <stage> review` or `no` (if fix is self-evident and preset allows).

If **Proceed** and there are **no** blocking findings, use **one sentinel row** with `—` in every column (do not write `(none)` or other placeholder text — those are parsed as real rows and fail validation).

## Non-blocking / follow-ups

| Summary | Suggested timeframe |
|---------|---------------------|
| | |

## Questions needing human/spec clarification

-

## Consensus / disagreements among reviewers

[Call out debates; do not bury dissent]
