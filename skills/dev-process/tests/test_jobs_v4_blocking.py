"""Blocking fixes: path safety, pre-v4 guard, duplicate session at close, generated paths."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
PY = sys.executable

HANDOFF_BODY = """# Handoff

## Approved facts
Spec and plan artifacts are approved for the next job.

## Artifact paths
- spec: 0001_spec.md

## Decisions
Proceed with standard preset for this stage.

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


def test_task_start_refuses_pre_v4_without_force(tmp_path: Path) -> None:
    old = tmp_path / "old_task"
    old.mkdir()
    (old / "state.yaml").write_text(
        "task_id: old_task\ncurrent_stage: plan\n",
        encoding="utf-8",
    )
    r = _run("run_dp.py", "task", "start", "--task-dir", str(old))
    assert r.returncode == 2
    assert "pre-v4" in r.stderr.lower()
    assert not (old / "jobs.yaml").is_file()


def test_duplicate_session_rejected_at_close(tmp_path: Path) -> None:
    task = tmp_path / "t_dup"
    _run("run_dp.py", "task", "start", "--task-dir", str(task))
    export = tmp_path / "s.jsonl"
    export.write_text(json.dumps({"id": "215735", "model": "m"}) + "\n", encoding="utf-8")

    r0 = _run("dp_job_start.py", "--task-dir", str(task), "--role", "spec", "--print-json")
    _write_handoff(task / json.loads(r0.stdout)["handoff_out"])
    assert _run("dp_job_close.py", "--task-dir", str(task), "--session-export", str(export)).returncode == 0

    r1 = _run(
        "dp_job_start.py",
        "--task-dir",
        str(task),
        "--role",
        "plan",
        "--handoff-in",
        json.loads(r0.stdout)["handoff_out"],
        "--print-json",
    )
    _write_handoff(task / json.loads(r1.stdout)["handoff_out"])
    r2 = _run("dp_job_close.py", "--task-dir", str(task), "--session-export", str(export))
    assert r2.returncode == 2
    assert "J1" in r2.stderr or "already used" in r2.stderr


def test_short_session_id_accepted(tmp_path: Path) -> None:
    task = tmp_path / "t_short"
    _run("run_dp.py", "task", "start", "--task-dir", str(task))
    export = tmp_path / "s.jsonl"
    export.write_text(json.dumps({"id": "215735"}) + "\n", encoding="utf-8")
    _run("dp_job_start.py", "--task-dir", str(task), "--role", "spec", "--print-json")
    jobs = yaml.safe_load((task / "jobs.yaml").read_text(encoding="utf-8"))
    _write_handoff(task / jobs["jobs"][0]["handoff_out"])
    r = _run("dp_job_close.py", "--task-dir", str(task), "--session-export", str(export))
    assert r.returncode == 0, r.stderr


def test_render_writes_generated_dir(tmp_path: Path) -> None:
    task = tmp_path / "t_gen"
    _run("run_dp.py", "task", "start", "--task-dir", str(task))
    export = tmp_path / "s.jsonl"
    export.write_text(json.dumps({"id": "sess_abc", "model": "m"}) + "\n", encoding="utf-8")
    _run("dp_job_start.py", "--task-dir", str(task), "--role", "spec", "--print-json")
    jobs = yaml.safe_load((task / "jobs.yaml").read_text(encoding="utf-8"))
    _write_handoff(task / jobs["jobs"][0]["handoff_out"])
    _run("dp_job_close.py", "--task-dir", str(task), "--session-export", str(export))
    r = _run("render_jobs.py", "model-usage", "--task-dir", str(task))
    assert r.returncode == 0
    out = task / "generated" / "model_usage.md"
    assert out.is_file()
    assert not (task / "0000_model_usage.md").exists()


def test_path_traversal_handoff_in_rejected(tmp_path: Path) -> None:
    task = tmp_path / "t_path"
    export = tmp_path / "e.jsonl"
    export.write_text(json.dumps({"id": "sess_path_test"}) + "\n", encoding="utf-8")
    _run("run_dp.py", "task", "start", "--task-dir", str(task))
    _run("dp_job_start.py", "--task-dir", str(task), "--role", "spec", "--print-json")
    jobs = yaml.safe_load((task / "jobs.yaml").read_text(encoding="utf-8"))
    _write_handoff(task / jobs["jobs"][0]["handoff_out"])
    _run("dp_job_close.py", "--task-dir", str(task), "--session-export", str(export))

    r = _run(
        "dp_job_start.py",
        "--task-dir",
        str(task),
        "--role",
        "plan",
        "--handoff-in",
        "../../etc/passwd",
    )
    assert r.returncode == 2
