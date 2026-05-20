"""Drift tests for review_targets.yaml vs review/agents and review/presets.md."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "review" / "agents"
PRESETS_MD = ROOT / "review" / "presets.md"
TARGETS_YAML = ROOT / "config" / "review_targets.yaml"


def _agent_files() -> set[str]:
    return {p.stem for p in AGENTS_DIR.glob("*.md") if p.stem != "synthesis"}


def _load_targets() -> dict:
    with TARGETS_YAML.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_agents_match_review_agents_dir() -> None:
    targets = _load_targets()
    yaml_agents = set(targets["agents"])
    assert (
        yaml_agents == _agent_files()
    ), f"review_targets agents drift: yaml={yaml_agents} files={_agent_files()}"


def test_deep_required_reviewers_in_presets_md() -> None:
    presets_text = PRESETS_MD.read_text(encoding="utf-8")
    deep = _load_targets()["presets"]["deep"]["required_reviewers"]
    for agent in deep:
        assert (
            agent in presets_text
        ), f"deep required reviewer {agent!r} not found in presets.md"


def test_light_and_standard_reviewers_in_presets_md() -> None:
    presets_text = PRESETS_MD.read_text(encoding="utf-8")
    for preset_name in ("light", "standard"):
        for agent in _load_targets()["presets"][preset_name]["required_reviewers"]:
            assert (
                agent in presets_text
            ), f"{preset_name} reviewer {agent!r} not found in presets.md"


def test_synthesis_actions_are_policy_actions() -> None:
    with (ROOT / "config" / "model_policy.yaml").open(encoding="utf-8") as f:
        policy = yaml.safe_load(f)
    actions = set((policy.get("action_overrides") or {}).keys())
    targets = _load_targets()
    for preset_name, cfg in targets["presets"].items():
        syn = cfg.get("synthesis_action")
        assert (
            syn in actions
        ), f"preset {preset_name} synthesis_action {syn!r} missing from model_policy"
