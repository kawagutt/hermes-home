"""Consistency tests for primary_segments.yaml vs model_policy.yaml."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
SCRIPTS = ROOT / "scripts"

import sys

sys.path.insert(0, str(SCRIPTS))

from model_resolve import load_yaml, resolve_for_task, validate_policy  # noqa: E402
from validate_model_governance import (  # noqa: E402
    expand_implementation_phase_ids,
    implementation_usage_stage_ids,
    load_primary_segments,
    resolve_required_usage_stage_ids,
)


def _minimal_task(tmp_path: Path) -> Path:
    task = tmp_path / "task"
    task.mkdir()
    (task / "state.yaml").write_text(
        'task_id: "20260520_seg"\ncurrent_stage: "spec"\n'
        'review_depth_preset: "standard"\n',
        encoding="utf-8",
    )
    return task


def test_primary_segments_actions_match_policy() -> None:
    policy = validate_policy(load_yaml(CONFIG / "model_policy.yaml"))
    action_overrides = policy["action_overrides"]
    profiles = policy["profiles"]
    segments = load_primary_segments()["segments"]
    assert isinstance(segments, dict)
    for preset_name, preset_cfg in segments.items():
        static = preset_cfg.get("static") or []
        for entry in static:
            action = entry["action"]
            role = entry["profile_role"]
            assert action in action_overrides, f"{preset_name} static {action}"
            assert action_overrides[action] == role
            assert role in profiles
        impl = (preset_cfg.get("dynamic") or {}).get("implementation_phases") or {}
        if impl:
            action = impl["action"]
            role = impl["profile_role"]
            assert action in action_overrides
            assert action_overrides[action] == role
            assert role in profiles


def test_primary_usage_stage_ids_resolve_via_dp_helpers(tmp_path: Path) -> None:
    task = _minimal_task(tmp_path)
    policy_path = CONFIG / "model_policy.yaml"
    segments = load_primary_segments()
    state = {
        "review_depth_preset": "standard",
        "review_rounds": {},
        "current_phase": "",
        "artifacts": {},
    }
    required = resolve_required_usage_stage_ids(state, task, segments)
    assert "spec" in required
    assert "implementation" in required
    assert "spec_review" not in required

    for uid in required:
        r = resolve_for_task(task, policy_path=policy_path, stage_id=uid)
        assert r["hermes_profile"]
        assert r["role"]


def test_expand_implementation_phases_from_review_rounds() -> None:
    state = {
        "review_rounds": {"implementation_phase_01": 1, "implementation_phase_02": 0},
        "current_phase": "",
        "artifacts": {},
    }
    ids = expand_implementation_phase_ids(
        state, Path("/tmp"), "implementation_phase_{phase}"
    )
    assert ids == ["implementation_phase_01"]


def test_implementation_usage_ids_phase_or_fallback_not_both() -> None:
    with_phases = {
        "review_rounds": {"implementation_phase_01": 1},
        "current_phase": "",
        "artifacts": {},
    }
    ids = implementation_usage_stage_ids(
        with_phases, Path("/tmp"), "implementation_phase_{phase}"
    )
    assert ids == ["implementation_phase_01"]
    assert "implementation" not in ids

    no_phases = {"review_rounds": {}, "current_phase": "", "artifacts": {}}
    ids = implementation_usage_stage_ids(
        no_phases, Path("/tmp"), "implementation_phase_{phase}"
    )
    assert ids == ["implementation"]


def test_resolve_required_no_duplicate_implementation(tmp_path: Path) -> None:
    task = _minimal_task(tmp_path)
    state = {
        "review_depth_preset": "standard",
        "review_rounds": {"implementation_phase_01": 1},
        "current_phase": "",
        "artifacts": {},
    }
    required = resolve_required_usage_stage_ids(
        state, task, load_primary_segments()
    )
    assert "implementation_phase_01" in required
    assert "implementation" not in required
