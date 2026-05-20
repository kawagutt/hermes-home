"""Tests for validate_model_governance.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))

from validate_model_governance import (  # noqa: E402
    infer_model_usage_required,
    parse_session_id,
    parse_model_usage_table,
)


def run_gov(task_dir: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / "validate_model_governance.py"), str(task_dir)]
    cmd.extend(extra)
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def _session(n: int) -> str:
    return f"20260520_{n:06d}_{n:06x}"


def _model_usage_row(stage: str, sid: str) -> str:
    session_cell = sid if sid == "unknown" else f"`{sid}`"
    return (
        f"| t | `{stage}` | act | p / r | std / med | {session_cell} | m | u | e |"
    )


def make_governance_task(
    tmp_path: Path,
    *,
    bad_duplicate: bool = False,
    unknown_spec: bool = False,
    timeline_waiver: bool = False,
    with_phase: bool = False,
) -> Path:
    task = tmp_path / "20260520_govtest"
    task.mkdir()
    stages = ["spec", "plan", "test", "implementation", "final_review", "final_summary"]
    if with_phase:
        stages = ["spec", "plan", "test", "implementation_phase_01", "final_review", "final_summary"]
    rows = []
    sid = _session(1)
    for i, st in enumerate(stages):
        if unknown_spec and st == "spec":
            s = "unknown"
        elif bad_duplicate and i > 0:
            s = sid
        else:
            s = _session(i + 1)
        rows.append(_model_usage_row(st, s))
    (task / "0010_model_usage.md").write_text(
        "| Time | Stage id | Action | Profile / role | Preset / reasoning | Session | Model | Usage / cost | Evidence |\n"
        "|------|----------|--------|----------------|-------------------|---------|-------|--------------|----------|\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )
    (task / "0005_plan.md").write_text(
        "| Field | Value |\n|-------|-------|\n"
        "| **Model usage record required?** | yes |\n"
        "| **Selected review-depth preset** | `standard` |\n",
        encoding="utf-8",
    )
    timeline = "| Time | Stage | Action | Output |\n|---|---|---|---|\n"
    if timeline_waiver:
        timeline += (
            "| t | spec | model usage waiver | spec Session unknown; PyYAML helper fixed later |\n"
        )
    (task / "0001_timeline.md").write_text(timeline, encoding="utf-8")

    round_dir = task / "reviews" / "spec" / "round_01"
    round_dir.mkdir(parents=True)
    manifest = f"""review_stage: spec
round: 1
preset: standard
reviewers:
  checklist_compliance:
    action: review_checklist_compliance
    role: review_main
    hermes_profile: dp-review
    output: checklist_compliance.md
    session_id: "{_session(10)}"
    usage_evidence: export
  requirements:
    action: review_requirements
    role: review_main
    hermes_profile: dp-review
    output: requirements.md
    session_id: "{_session(11)}"
    usage_evidence: export
  diff_detail:
    action: review_diff_detail
    role: review_main
    hermes_profile: dp-review
    output: diff_detail.md
    session_id: "{_session(12)}"
    usage_evidence: export
synthesis:
  action: review_synthesis_standard
  role: review_main
  hermes_profile: dp-review
  output: synthesis.md
  session_id: "{_session(13)}"
  usage_evidence: export
"""
    (round_dir / "review_manifest.yaml").write_text(manifest, encoding="utf-8")

    review_rounds = """
  spec: 1
  plan: 0
  test: 0
  final: 0
"""
    if with_phase:
        review_rounds = """
  spec: 1
  plan: 0
  test: 0
  final: 0
  implementation_phase_01: 1
"""

    (task / "state.yaml").write_text(
        f"""
task_id: "20260520_govtest"
current_stage: "final"
review_depth_preset: "standard"
model_usage_required: true
last_hermes_profile: "dp-strong"
artifacts:
  plan: "0005_plan.md"
  model_usage: "0010_model_usage.md"
  timeline: "0001_timeline.md"
review_rounds:{review_rounds}
""".lstrip(),
        encoding="utf-8",
    )
    return task


def test_parse_session_id_accepts_backtick_and_plain() -> None:
    assert parse_session_id("`20260520_001817_f70907`") == "20260520_001817_f70907"
    assert parse_session_id("20260520_001817_f70907") == "20260520_001817_f70907"
    assert parse_session_id("unknown") is None


def test_infer_model_usage_required_from_preset() -> None:
    state = {"review_depth_preset": "deep", "model_usage_required": None}
    assert infer_model_usage_required(state, Path("/tmp")) is True
    state["review_depth_preset"] = "light"
    state["model_usage_required"] = False
    assert infer_model_usage_required(state, Path("/tmp")) is False


def test_validate_strict_ok(tmp_path: Path) -> None:
    task = make_governance_task(tmp_path)
    r = run_gov(task, "--strict")
    assert r.returncode == 0, r.stdout + r.stderr


def test_validate_strict_ok_with_phase(tmp_path: Path) -> None:
    task = make_governance_task(tmp_path, with_phase=True)
    r = run_gov(task, "--strict")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "implementation_phase_01" in (task / "0010_model_usage.md").read_text()


def test_validate_strict_duplicate_session(tmp_path: Path) -> None:
    task = make_governance_task(tmp_path, bad_duplicate=True)
    r = run_gov(task, "--strict")
    assert r.returncode == 1
    assert "duplicate primary session_id" in r.stdout


def test_validate_strict_unknown_with_waiver(tmp_path: Path) -> None:
    task = make_governance_task(tmp_path, unknown_spec=True, timeline_waiver=True)
    r = run_gov(task, "--strict")
    assert r.returncode == 0, r.stdout + r.stderr


def test_validate_strict_unknown_without_waiver_fails(tmp_path: Path) -> None:
    task = make_governance_task(tmp_path, unknown_spec=True, timeline_waiver=False)
    r = run_gov(task, "--strict")
    assert r.returncode == 1
    assert "unresolved unknown Session for stage spec" in r.stdout


def test_validate_manifest_synthesis_same_as_reviewer(tmp_path: Path) -> None:
    task = make_governance_task(tmp_path)
    manifest = task / "reviews" / "spec" / "round_01" / "review_manifest.yaml"
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(
        text.replace(_session(13), _session(10)),
        encoding="utf-8",
    )
    r = run_gov(task, "--strict")
    assert r.returncode == 1
    assert "synthesis session_id must differ" in r.stdout


def test_parse_model_usage_table_finds_session_column() -> None:
    text = (
        "| Time | Stage id | Action | Profile / role | Preset / reasoning | Session | Model | Usage / cost | Evidence |\n"
        "| t | `spec` | a | p | pr | `20260520_000001_a1b2c1` | m | u | e |\n"
    )
    rows, errs = parse_model_usage_table(text)
    assert not errs
    assert rows["spec"] == "20260520_000001_a1b2c1"
