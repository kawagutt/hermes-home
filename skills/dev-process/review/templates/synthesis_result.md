# Synthesis template

Written as **`synthesis.md`** inside **`.hermes/tasks/<task-id>/reviews/<stage>/round_NN/`** — one round per review run (**never overwrite** previous `round_*` dirs). **Do not** use `NNNN_` prefixes under `reviews/` (task-root only; see [`artifacts/SKILL.md`](../../artifacts/SKILL.md#numbered-task-root-artifacts) § Numbered task-root artifacts).

## Meta

- Task ID: `[YYYYMMDD_short-slug]`  
- Stage: `[spec | plan | test | implementation_phase_NN | final]`  
- Review round: `[round_01]` — must match subdirectory name.  
- Date: `[ISO date]`  

## Recommendation

Pick one primary:

- [ ] Proceed  
- [ ] Rework tests  
- [ ] Rework plan  
- [ ] Rework implementation  
- [ ] Stop — human decision required  

**One-line rationale:**

[Sentence]

## Rework owner (blocking findings)

For **each blocking** finding, assign **one** owner and the **next operational step**. Do not leave “needs fix” without an owner stage.

| ID source | Summary | Owner | Required next step |
|-----------|---------|-------|---------------------|
| e.g. F1 architecture | … | spec / plan / test / implementation / human | e.g. Return to PlanAgent → plan review |
| | | | |

**Owner values:** `spec` | `plan` | `test` | `implementation` | `human`

## Non-blocking / follow-ups

| Summary | Suggested timeframe |
|---------|---------------------|
| | |

## Questions needing human/spec clarification

-

## Consensus / disagreements among reviewers

[Call out debates; do not bury dissent]
