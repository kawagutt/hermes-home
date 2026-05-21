"""Tests for v4 Job Contract helpers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
PY = sys.executable

HANDOFF_BODY = """# Handoff

## Approved facts
Spec approved for implementation.

## Artifact paths
- spec: 0001_spec.md

## Decisions
Proceed with standard preset.

## Open items
No blocking items for the next job.
"""


def _run(script: str, *argv: str) -> subprocess.CompletedProcess[str]:
    env = {"PYTHONPATH": str(SCRIPTS)}
    return subprocess.run(
        [PY, str(SCRIPTS / script), *argv],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )


def _write_handoff(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HANDOFF_BODY, encoding="utf-8")


@pytest.fixture
def v4_task(tmp_path: Path) -> Path:
    task = tmp_path / "20260521_test-v4"
    r = _run("run_dp.py", "task", "start", "--task-dir", str(task))
    assert r.returncode == 0, r.stderr
    return task


def test_task_start_creates_jobs_yaml(v4_task: Path) -> None:
    jobs = v4_task / "jobs.yaml"
    assert jobs.is_file()
    data = yaml.safe_load(jobs.read_text(encoding="utf-8"))
    assert data["schema_version"] == 4
    assert data["jobs"] == []


def test_first_job_id_is_job_0000(v4_task: Path) -> None:
    r = _run(
        "dp_job_start.py",
        "--task-dir",
        str(v4_task),
        "--role",
        "spec",
        "--print-json",
    )
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["job_id"] == "job_0000"


def test_job_start_close_cycle(v4_task: Path, tmp_path: Path) -> None:
    r = _run(
        "dp_job_start.py",
        "--task-dir",
        str(v4_task),
        "--role",
        "spec",
        "--print-json",
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert payload["job_id"] == "job_0000"
    handoff_out = v4_task / payload["handoff_out"]
    _write_handoff(handoff_out)
    (v4_task / "0001_spec.md").write_text("# spec\n", encoding="utf-8")

    export = tmp_path / "sess.jsonl"
    export.write_text(
        json.dumps(
            {
                "id": "20260521_120000_abcdef",
                "model": "gpt-test",
                "input_tokens": 10,
                "output_tokens": 5,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    r2 = _run(
        "dp_job_close.py",
        "--task-dir",
        str(v4_task),
        "--session-export",
        str(export),
        "--artifacts-out",
        "spec=0001_spec.md",
    )
    assert r2.returncode == 0, r.stderr

    data = yaml.safe_load((v4_task / "jobs.yaml").read_text(encoding="utf-8"))
    job = data["jobs"][0]
    assert job["status"] == "closed"
    assert job["session_id"] == "20260521_120000_abcdef"
    assert job["handoff_in"] == []


def test_plan_requires_handoff_in(v4_task: Path) -> None:
    r = _run(
        "dp_job_start.py",
        "--task-dir",
        str(v4_task),
        "--role",
        "plan",
    )
    assert r.returncode == 2
    assert "handoff-in" in r.stderr.lower()


def test_j1_duplicate_session_rejected_on_second_close(v4_task: Path, tmp_path: Path) -> None:
    export = tmp_path / "s.jsonl"
    export.write_text(
        json.dumps({"id": "20260521_120000_abcdef", "model": "m"}) + "\n",
        encoding="utf-8",
    )
    r0 = _run("dp_job_start.py", "--task-dir", str(v4_task), "--role", "spec", "--print-json")
    spec_out = json.loads(r0.stdout)["handoff_out"]
    _write_handoff(v4_task / spec_out)
    assert _run("dp_job_close.py", "--task-dir", str(v4_task), "--session-export", str(export)).returncode == 0

    r1 = _run(
        "dp_job_start.py",
        "--task-dir",
        str(v4_task),
        "--role",
        "plan",
        "--handoff-in",
        spec_out,
        "--print-json",
    )
    assert r1.returncode == 0, r1.stderr
    _write_handoff(v4_task / json.loads(r1.stdout)["handoff_out"])
    r2 = _run("dp_job_close.py", "--task-dir", str(v4_task), "--session-export", str(export))
    assert r2.returncode == 2
    assert "J1" in r2.stderr or "already used" in r2.stderr


def test_close_rejects_empty_handoff(v4_task: Path, tmp_path: Path) -> None:
    _run("dp_job_start.py", "--task-dir", str(v4_task), "--role", "spec")
    export = tmp_path / "s.jsonl"
    export.write_text(json.dumps({"id": "20260521_120001_aaaaaa"}) + "\n", encoding="utf-8")
    r = _run("dp_job_close.py", "--task-dir", str(v4_task), "--session-export", str(export))
    assert r.returncode == 2
    assert "handoff_out" in r.stderr.lower()


def test_validate_pre_v4_skips(tmp_path: Path) -> None:
    task = tmp_path / "old_task"
    task.mkdir()
    (task / "state.yaml").write_text("task_id: old_task\n", encoding="utf-8")
    r = _run("validate_jobs_v4.py", str(task))
    assert r.returncode == 0
    assert "pre-v4" in r.stderr


def test_validate_pre_v4_strict_exits_zero(tmp_path: Path) -> None:
    task = tmp_path / "old_task"
    task.mkdir()
    (task / "state.yaml").write_text("task_id: old_task\n", encoding="utf-8")
    r = _run("validate_jobs_v4.py", str(task), "--strict")
    assert r.returncode == 0
    assert "not applicable" in r.stderr.lower()


def test_close_rejects_missing_artifacts_out(v4_task: Path, tmp_path: Path) -> None:
    _run("dp_job_start.py", "--task-dir", str(v4_task), "--role", "spec")
    jobs = yaml.safe_load((v4_task / "jobs.yaml").read_text(encoding="utf-8"))
    _write_handoff(v4_task / jobs["jobs"][0]["handoff_out"])
    export = tmp_path / "s.jsonl"
    export.write_text(json.dumps({"id": "sess_missing_art"}) + "\n", encoding="utf-8")
    r = _run(
        "dp_job_close.py",
        "--task-dir",
        str(v4_task),
        "--session-export",
        str(export),
        "--artifacts-out",
        "spec=0001_spec.md",
    )
    assert r.returncode == 2
    assert "missing" in r.stderr.lower()


def test_review_round_zero_rejected(v4_task: Path) -> None:
    hin = v4_task / "handoffs" / "brief_plan.md"
    _write_handoff(hin)
    r = _run(
        "dp_job_start.py",
        "--task-dir",
        str(v4_task),
        "--role",
        "review_worker",
        "--handoff-in",
        str(hin.relative_to(v4_task)),
        "--reviewer",
        "requirements",
        "--review-target",
        "plan",
        "--review-round",
        "0",
    )
    assert r.returncode == 2
    assert "review_round" in r.stderr.lower()
