"""validate_state.py skips pre-v4 governance preflight on v4 tasks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
PY = sys.executable


def _run_validate(task: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, str(SCRIPTS / "validate_state.py"), str(task)],
        capture_output=True,
        text=True,
    )


def test_v4_task_skips_last_hermes_preflight(tmp_path: Path) -> None:
    task = tmp_path / "20260521_v4"
    task.mkdir()
    (task / "jobs.yaml").write_text(
        "schema_version: 4\ntask_id: 20260521_v4\njobs: []\n",
        encoding="utf-8",
    )
    state = {
        "task_id": "20260521_v4",
        "current_stage": "final",
        "review_depth_preset": "deep",
        "model_usage_required": True,
        "reviewed": {"final": True},
        "approved": {"final_human_gate": False},
        "pending_human_gate": "final_human_gate",
        "artifacts": {"spec": "0001_spec.md"},
        "branch": {
            "name": "dev-process/x",
            "feasibility_checked_before_human_spec_gate": True,
            "task_branch_precondition_met": True,
            "commits_allowed_on_task_branch": True,
            "task_artifacts_commit_by_default": False,
        },
    }
    (task / "state.yaml").write_text(yaml.safe_dump(state), encoding="utf-8")
    (task / "0001_spec.md").write_text("# spec\n", encoding="utf-8")

    r = _run_validate(task)
    assert "last_hermes_profile" not in r.stdout
    assert "governance preflight: missing last_hermes_profile" not in r.stdout
