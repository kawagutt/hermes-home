"""Round-2 blocking fixes: review strict, profile observation, render on close."""

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
Artifacts approved for the next job.

## Artifact paths
- spec: 0001_spec.md

## Decisions
Proceed with standard preset.

## Open items
No blocking items for the next job.
"""


def _run(script: str, *argv: str) -> subprocess.CompletedProcess[str]:
    env = {
        **__import__("os").environ,
        "PYTHONPATH": str(SCRIPTS),
        "DEV_PROCESS_NO_PROFILE_PROBE": "1",
    }
    return subprocess.run(
        [PY, str(SCRIPTS / script), *argv],
        capture_output=True,
        text=True,
        env=env,
    )


def _write_handoff(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HANDOFF_BODY, encoding="utf-8")


def _close_open_job(task: Path, export: Path) -> None:
    jobs = yaml.safe_load((task / "jobs.yaml").read_text(encoding="utf-8"))
    j = jobs["jobs"][-1]
    if j.get("handoff_out"):
        _write_handoff(task / j["handoff_out"])
    assert _run("dp_job_close.py", "--task-dir", str(task), "--session-export", str(export)).returncode == 0


def test_profile_mismatch_rejected_at_close(tmp_path: Path) -> None:
    task = tmp_path / "t_prof"
    _run("run_dp.py", "task", "start", "--task-dir", str(task))
    export = tmp_path / "s.jsonl"
    export.write_text(
        json.dumps({"id": "sess_prof", "hermes_profile": "dp-code-main"}) + "\n",
        encoding="utf-8",
    )
    _run("dp_job_start.py", "--task-dir", str(task), "--role", "spec", "--print-json")
    jobs = yaml.safe_load((task / "jobs.yaml").read_text(encoding="utf-8"))
    _write_handoff(task / jobs["jobs"][0]["handoff_out"])
    r = _run("dp_job_close.py", "--task-dir", str(task), "--session-export", str(export))
    assert r.returncode == 2
    assert "mismatch" in r.stderr.lower()


def test_strict_reviewed_spec_requires_all_reviewers(tmp_path: Path) -> None:
    task = tmp_path / "t_rev"
    _run("run_dp.py", "task", "start", "--task-dir", str(task))
    export = tmp_path / "s.jsonl"
    export.write_text(json.dumps({"id": "sess_rev", "model": "m"}) + "\n", encoding="utf-8")

    _run("dp_job_start.py", "--task-dir", str(task), "--role", "spec", "--print-json")
    _close_open_job(task, export)

    state_path = task / "state.yaml"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    state["reviewed"] = {"spec": True}
    state["review_rounds"] = {"spec": 1}
    state["review_depth_preset"] = "standard"
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    spec_out = yaml.safe_load((task / "jobs.yaml").read_text(encoding="utf-8"))["jobs"][0][
        "handoff_out"
    ]
    ex_w = tmp_path / "w.jsonl"
    ex_w.write_text(json.dumps({"id": "sess_w"}) + "\n", encoding="utf-8")
    _run(
        "dp_job_start.py",
        "--task-dir",
        str(task),
        "--role",
        "review_worker",
        "--handoff-in",
        spec_out,
        "--reviewer",
        "requirements",
        "--review-target",
        "spec",
        "--review-round",
        "1",
    )
    _close_open_job(task, ex_w)

    ex_s = tmp_path / "syn.jsonl"
    ex_s.write_text(json.dumps({"id": "sess_syn"}) + "\n", encoding="utf-8")
    _run(
        "dp_job_start.py",
        "--task-dir",
        str(task),
        "--role",
        "review_synthesis",
        "--handoff-in",
        spec_out,
        "--review-target",
        "spec",
        "--review-round",
        "1",
    )
    _close_open_job(task, ex_s)

    r = _run("validate_jobs_v4.py", str(task), "--strict")
    assert r.returncode != 0
    err = r.stderr.lower()
    assert "checklist_compliance" in err or "diff_detail" in err


def test_run_dp_validate_pre_v4_strict_zero(tmp_path: Path) -> None:
    task = tmp_path / "legacy"
    task.mkdir()
    (task / "state.yaml").write_text("task_id: legacy\ncurrent_stage: plan\n", encoding="utf-8")
    r = _run("run_dp.py", "validate", "--task-dir", str(task), "--strict")
    assert r.returncode == 0
