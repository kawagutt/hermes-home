# Rework log

One entry per **blocking** rework cycle (link to synthesis and round). Expand with `## R2`, `## R3`, … as needed.

## R1

- **Source:** e.g. `reviews/plan/round_01/synthesis.md`
- **Finding:** e.g. `F1` (from reviewer table)
- **Classification:** blocking / non-blocking (if reworked anyway)
- **Owner:** `spec` | `plan` | `test` | `implementation` | `human`
- **Required action:**
- **Fixed by:** agent or human role
- **Changed artifacts:**
  - `artifacts.plan` (as recorded in `state.yaml`)
  - `artifacts.phase_checklists`
- **Rerun:** paths to **new round** reviewer outputs e.g.
  - `reviews/plan/round_02/architecture.md`
  - `reviews/plan/round_02/checklist_compliance.md`
  - `reviews/plan/round_02/impact.md`
  - `reviews/plan/round_02/synthesis.md`
- **Result:** cleared | blocked | superseded by R2 …
