"""Tests for small deterministic dev-process helper utilities."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "dev-process" / "scripts"


def run_helper(
    name: str, *args: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        cwd=str(cwd or ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def make_task(tmp_path: Path) -> Path:
    task = tmp_path / ".hermes" / "tasks" / "20260510_example"
    (task / "reviews" / "spec" / "round_01").mkdir(parents=True)
    (task / "0000_spec.md").write_text("# Spec\n", encoding="utf-8")
    (task / "0001_timeline.md").write_text(
        "| Time | Stage | Action | Output |\n|---|---|---|---|\n",
        encoding="utf-8",
    )
    (task / "reviews" / "spec" / "round_01" / "synthesis.md").write_text(
        "# Synthesis\n", encoding="utf-8"
    )
    (task / "state.yaml").write_text(
        """
task_id: "20260510_example"
current_stage: "plan"
current_phase: ""
approved:
  spec: true
  human_spec_gate: true
  final_human_gate: false
reviewed:
  spec: true
  plan: false
  tests: false
  final: false
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
""".lstrip(),
        encoding="utf-8",
    )
    return task


def test_validate_state_reports_ok_and_missing_artifact(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    ok = run_helper("validate_state.py", str(task))
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "OK" in ok.stdout

    (task / "0000_spec.md").unlink()
    bad = run_helper("validate_state.py", str(task))
    assert bad.returncode == 1
    assert "missing artifact" in bad.stdout


def test_validate_state_detects_latest_review_round_mismatch(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    state = task / "state.yaml"
    state.write_text(
        state.read_text(encoding="utf-8").replace(
            'spec: "reviews/spec/round_01/synthesis.md"',
            'spec: "reviews/spec/round_02/synthesis.md"',
        ),
        encoding="utf-8",
    )
    bad = run_helper("validate_state.py", str(task))
    assert bad.returncode == 1
    assert "latest review round mismatch" in bad.stdout


def test_validate_state_detects_unnumbered_task_root_markdown(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    state = task / "state.yaml"
    (task / "spec.md").write_text("# Legacy spec\n", encoding="utf-8")
    state.write_text(
        state.read_text(encoding="utf-8").replace(
            'spec: "0000_spec.md"', 'spec: "spec.md"'
        ),
        encoding="utf-8",
    )
    bad = run_helper("validate_state.py", str(task))
    assert bad.returncode == 1
    assert "not numbered NNNN_<stem>.md" in bad.stdout


def test_review_round_helper_create_does_not_update_state_then_finish_does(
    tmp_path: Path,
) -> None:
    task = make_task(tmp_path)
    dry = run_helper("review_round.py", str(task), "plan", "--dry-run")
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert "round_01" in dry.stdout
    assert not (task / "reviews" / "plan" / "round_01").exists()

    created = run_helper("review_round.py", str(task), "plan", "--create")
    assert created.returncode == 0, created.stdout + created.stderr
    assert (task / "reviews" / "plan" / "round_01").exists()
    duplicate = run_helper("review_round.py", str(task), "plan", "--create")
    assert duplicate.returncode == 1
    assert "review round already exists" in duplicate.stdout
    state_after_create = (task / "state.yaml").read_text(encoding="utf-8")
    assert "plan: 0" in state_after_create
    assert "reviews/plan/round_01/synthesis.md" not in state_after_create

    incomplete = run_helper("review_round.py", str(task), "plan", "--finish")
    assert incomplete.returncode == 1
    assert "synthesis is missing or appears incomplete" in incomplete.stdout

    (task / "reviews" / "plan" / "round_01" / "synthesis.md").write_text(
        "# Synthesis\n\nRecommendation: proceed\n",
        encoding="utf-8",
    )
    no_heading = run_helper("review_round.py", str(task), "plan", "--finish")
    assert no_heading.returncode == 1
    assert "synthesis is missing or appears incomplete" in no_heading.stdout

    (task / "reviews" / "plan" / "round_01" / "synthesis.md").write_text(
        "# Synthesis\n\n## Recommendation\n\n- [x] Proceed\n",
        encoding="utf-8",
    )
    finished = run_helper("review_round.py", str(task), "plan", "--finish")
    assert finished.returncode == 0, finished.stdout + finished.stderr
    state_after_finish = (task / "state.yaml").read_text(encoding="utf-8")
    assert "plan: 1" in state_after_finish
    assert "reviews/plan/round_01/synthesis.md" in state_after_finish


def test_branch_precondition_dry_run_and_apply_updates_state_and_timeline(
    tmp_path: Path,
) -> None:
    task = make_task(tmp_path)
    branch = "dev-process/20260510_example"
    dry = run_helper(
        "branch_precondition.py", str(task), branch, "--dry-run", "--skip-git-check"
    )
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert "DRY-RUN" in dry.stdout
    assert "task_branch_precondition_met: false" in (task / "state.yaml").read_text(
        encoding="utf-8"
    )

    applied = run_helper(
        "branch_precondition.py",
        str(task),
        branch,
        "--apply",
        "--skip-git-check",
        "--evidence",
        "git switch -c dev-process/20260510_example",
    )
    assert applied.returncode == 0, applied.stdout + applied.stderr
    state = (task / "state.yaml").read_text(encoding="utf-8")
    assert "task_branch_precondition_met: true" in state
    assert "commits_allowed_on_task_branch: true" in state
    timeline = (task / "0001_timeline.md").read_text(encoding="utf-8")
    assert "| branch | Task branch precondition recorded |" in timeline
    assert "git switch -c dev-process/20260510_example" in timeline


def test_branch_precondition_checks_current_git_branch_by_default(
    tmp_path: Path,
) -> None:
    task = make_task(tmp_path)
    bad = run_helper(
        "branch_precondition.py",
        str(task),
        "not-current-branch",
        "--apply",
        "--repo",
        str(ROOT),
    )
    assert bad.returncode == 1
    assert "does not match expected task branch" in bad.stdout
