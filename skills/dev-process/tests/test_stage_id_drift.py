"""Detect drift between stage_ids.yaml, model_policy.yaml, and templates."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"


def _load_stage_ids() -> dict:
    with (CONFIG / "stage_ids.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _policy_usage_ids() -> set[str]:
    with (CONFIG / "model_policy.yaml").open(encoding="utf-8") as f:
        policy = yaml.safe_load(f)
    return set((policy.get("stage_actions") or {}).keys())


def _backtick_ids(text: str) -> set[str]:
    return set(re.findall(r"`([a-z][a-z0-9_]*)`", text))


def test_usage_stage_ids_match_policy_and_templates() -> None:
    canonical = set(_load_stage_ids()["usage_stage_ids"])
    policy_ids = _policy_usage_ids()
    model_usage = (ROOT / "templates" / "model_usage.md").read_text(encoding="utf-8")
    plan = (ROOT / "templates" / "plan.md").read_text(encoding="utf-8")

    table_section = plan.split("Optional per-stage table", 1)[-1]
    plan_ids = {
        sid
        for sid in _backtick_ids(table_section)
        if sid.endswith("_review")
        or sid.endswith("_gate")
        or sid in ("implementation", "final_summary")
    }

    assert (
        policy_ids == canonical
    ), f"model_policy stage_actions drift: {policy_ids ^ canonical}"
    assert (
        plan_ids == canonical
    ), f"plan.md optional table drift: {plan_ids ^ canonical}"


def test_model_usage_primary_examples_match_primary_usage_stage_ids() -> None:
    stage_ids = _load_stage_ids()
    primary = set(stage_ids["primary_usage_stage_ids"])
    model_usage = (ROOT / "templates" / "model_usage.md").read_text(encoding="utf-8")
    # Example rows between header and cumulative-values note.
    section = model_usage.split("**Cumulative values:**", 1)[0]
    table_lines = [
        ln for ln in section.splitlines() if ln.strip().startswith("|") and "`" in ln
    ]
    example_ids = set()
    for ln in table_lines:
        for sid in _backtick_ids(ln):
            if sid.endswith("_review") or sid.endswith("_gate"):
                continue
            example_ids.add(sid)
    # implementation_phase_01 is illustrative; primary list uses implementation fallback.
    example_ids.discard("implementation_phase_01")
    assert example_ids <= primary | {"implementation_phase_01"}, (
        f"model_usage primary examples drift: {example_ids - primary}"
    )
