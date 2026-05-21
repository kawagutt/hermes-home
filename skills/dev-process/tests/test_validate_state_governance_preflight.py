"""Tests for validate_state.py governance preflight (Task 5)."""

from __future__ import annotations

from test_helpers import make_task, run_helper


def _write_state(task, text: str) -> None:
    (task / "state.yaml").write_text(text, encoding="utf-8")


def _base_state(
    *,
    current_stage: str = "plan",
    final_reviewed: bool = False,
    final_gate_wait: bool = False,
) -> str:
    final_val = "true" if final_reviewed else "false"
    if final_gate_wait:
        pending = 'pending_human_gate: "final_human_gate"'
        gate_at = 'gate_prompted_at: "2026-05-21T12:00:00Z"'
    else:
        pending = 'pending_human_gate: ""'
        gate_at = 'gate_prompted_at: ""'
    return f"""
task_id: "20260510_example"
current_stage: "{current_stage}"
current_phase: ""
review_depth_preset: "standard"
model_usage_required: true
{pending}
{gate_at}
approved:
  human_spec_gate: true
  final_human_gate: false
reviewed:
  spec: true
  plan: false
  tests: false
  final: {final_val}
escalation:
  required: false
  reason: ""
review_rounds:
  spec: 1
  plan: 0
  test: 0
  final: 0
  implementation_phase_01: 0
latest_reviews:
  spec: "reviews/spec/round_01/synthesis.md"
  plan: ""
  test: ""
  final: ""
  implementation_phase_01: ""
branch:
  name: "dev-process/20260510_example"
  feasibility_checked_before_human_spec_gate: true
  feasibility_notes: "ok"
  task_branch_precondition_met: false
  commits_allowed_on_task_branch: false
  task_artifacts_commit_by_default: false
artifacts:
  spec: "0000_spec.md"
  spec_summary_ja: ""
  human_spec_gate: ""
  plan: ""
  phase_checklists: ""
  timeline: "0001_timeline.md"
  rework_log: ""
  test_plan: ""
  test_implementation: ""
  red_test_result: ""
  implementation_log: ""
  phase_results: ""
  final_test_result: ""
  final_summary_ja: ""
  final_human_gate: ""
""".lstrip()


def test_preflight_errors_missing_last_profile_at_final_review(tmp_path) -> None:
    task = make_task(tmp_path)
    _write_state(
        task,
        _base_state(final_reviewed=True, final_gate_wait=True),
    )

    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "governance preflight" in r.stdout
    assert "last_hermes_profile" in r.stdout
    assert "reviewed.final is true but pending_human_gate is not" not in r.stdout


def test_preflight_not_error_for_current_stage_final_alone(tmp_path) -> None:
    task = make_task(tmp_path)
    _write_state(task, _base_state(current_stage="final", final_reviewed=False))

    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "governance preflight" not in r.stdout
    assert "missing last_hermes_profile" in r.stdout
