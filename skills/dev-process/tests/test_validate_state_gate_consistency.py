"""Tests for validate_state.py human gate consistency checks."""

from __future__ import annotations

from pathlib import Path

from test_helpers import make_task, run_helper


def _patch_state(task: Path, *replacements: tuple[str, str]) -> None:
    state = task / "state.yaml"
    text = state.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    state.write_text(text, encoding="utf-8")


def test_gate_consistency_default_task_ok(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout
    assert "reviewed.final is true but" not in r.stdout


def test_spec_gate_wait_ok(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ('current_stage: "plan"', 'current_stage: "spec"'),
        ("human_spec_gate: true", "human_spec_gate: false"),
        ('pending_human_gate: ""', 'pending_human_gate: "human_spec_gate"'),
        ('gate_prompted_at: ""', 'gate_prompted_at: "2026-05-21T12:00:00Z"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "advanced past spec gate wait" not in r.stdout
    assert "reviewed.spec is true but pending_human_gate is not" not in r.stdout


def test_final_gate_wait_ok(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("final: false", "final: true"),
        ('current_stage: "plan"', 'current_stage: "final"'),
        ('pending_human_gate: ""', 'pending_human_gate: "final_human_gate"'),
        ('gate_prompted_at: ""', 'gate_prompted_at: "2026-05-21T12:00:00Z"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "pending_human_gate is final_human_gate but current_stage" not in r.stdout


def test_final_reviewed_missing_pending_error(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(task, ("final: false", "final: true"))
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "reviewed.final is true but pending_human_gate is not" in r.stdout


def test_final_reviewed_wrong_pending_gate_error(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("final: false", "final: true"),
        ('pending_human_gate: ""', 'pending_human_gate: "human_spec_gate"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "reviewed.final is true but pending_human_gate is not" in r.stdout


def test_spec_reviewed_missing_pending_error(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("human_spec_gate: true", "human_spec_gate: false"),
        ('pending_human_gate: ""', 'pending_human_gate: ""'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "reviewed.spec is true but pending_human_gate is not" in r.stdout


def test_spec_reviewed_wrong_pending_gate_error(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("human_spec_gate: true", "human_spec_gate: false"),
        ('pending_human_gate: ""', 'pending_human_gate: "final_human_gate"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "reviewed.spec is true but pending_human_gate is not" in r.stdout


def test_approved_human_spec_gate_with_pending_spec_error(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ('pending_human_gate: ""', 'pending_human_gate: "human_spec_gate"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "approved.human_spec_gate is already true" in r.stdout


def test_approved_final_with_pending_final_error(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("final_human_gate: false", "final_human_gate: true"),
        ('pending_human_gate: ""', 'pending_human_gate: "final_human_gate"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "approved.final_human_gate is already true" in r.stdout


def test_spec_approved_final_gate_wait_ok(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("final: false", "final: true"),
        ('pending_human_gate: ""', 'pending_human_gate: "final_human_gate"'),
        ('gate_prompted_at: ""', 'gate_prompted_at: "2026-05-21T12:00:00Z"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr


def test_pending_without_gate_prompted_at_warning(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("final: false", "final: true"),
        ('current_stage: "plan"', 'current_stage: "final"'),
        ('pending_human_gate: ""', 'pending_human_gate: "final_human_gate"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "gate_prompted_at is empty" in r.stdout


def test_spec_pending_at_plan_stage_warning(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("human_spec_gate: true", "human_spec_gate: false"),
        ('pending_human_gate: ""', 'pending_human_gate: "human_spec_gate"'),
        ('gate_prompted_at: ""', 'gate_prompted_at: "2026-05-21T12:00:00Z"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "advanced past spec gate wait" in r.stdout


def test_final_pending_at_completed_warning(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("final: false", "final: true"),
        ('current_stage: "plan"', 'current_stage: "completed"'),
        ('pending_human_gate: ""', 'pending_human_gate: "final_human_gate"'),
        ('gate_prompted_at: ""', 'gate_prompted_at: "2026-05-21T12:00:00Z"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "advanced past final gate wait" in r.stdout


def test_final_pending_at_unknown_stage_warning(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(
        task,
        ("final: false", "final: true"),
        ('current_stage: "plan"', 'current_stage: "merged_no_push"'),
        ('pending_human_gate: ""', 'pending_human_gate: "final_human_gate"'),
        ('gate_prompted_at: ""', 'gate_prompted_at: "2026-05-21T12:00:00Z"'),
    )
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "advanced past final gate wait" in r.stdout


def test_invalid_pending_human_gate_error(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    _patch_state(task, ('pending_human_gate: ""', 'pending_human_gate: "bogus_gate"'))
    r = run_helper("validate_state.py", str(task))
    assert r.returncode == 1
    assert "pending_human_gate 'bogus_gate' is invalid" in r.stdout
