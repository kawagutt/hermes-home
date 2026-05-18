"""Tests for validate_state.py model-handoff and current_stage checks."""

from __future__ import annotations

from test_helpers import make_task, run_helper


def test_validate_state_warns_missing_last_hermes_profile(tmp_path) -> None:
    task = make_task(tmp_path)
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "WARNING" in r.stdout
    assert "last_hermes_profile" in r.stdout


def test_validate_state_strict_fails_on_missing_last_hermes_profile(tmp_path) -> None:
    task = make_task(tmp_path)
    r = run_helper("validate_state.py", str(task), "--strict")
    assert r.returncode == 1
    assert "last_hermes_profile" in r.stdout


def test_validate_state_errors_usage_stage_as_current_stage(tmp_path) -> None:
    task = make_task(tmp_path)
    state = task / "state.yaml"
    state.write_text(
        state.read_text(encoding="utf-8").replace(
            'current_stage: "plan"', 'current_stage: "spec_review"'
        ),
        encoding="utf-8",
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "usage stage id only" in r.stdout
    assert "spec_review" in r.stdout
