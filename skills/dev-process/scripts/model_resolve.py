#!/usr/bin/env python3
"""Shared dev-process model/profile resolution from model_policy.yaml + task state."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


class ModelResolveError(Exception):
    """Policy or task resolution failure."""


def default_policy_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "model_policy.yaml"


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise ModelResolveError("PyYAML is required (pip install pyyaml)")
    if not path.is_file():
        raise ModelResolveError(f"policy file not found: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_task_state(task_dir: Path) -> dict[str, Any]:
    if yaml is None:
        raise ModelResolveError("PyYAML is required (pip install pyyaml)")
    state_path = task_dir / "state.yaml"
    if not state_path.is_file():
        raise ModelResolveError(f"state.yaml not found: {state_path}")
    with state_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ModelResolveError("state.yaml root must be a mapping")
    return data


def validate_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise ModelResolveError("policy root must be a mapping")
    if policy.get("schema_version") != 2:
        raise ModelResolveError("unsupported schema_version (expected 2)")

    for key in (
        "profiles",
        "stage_defaults",
        "action_overrides",
        "stage_actions",
        "reasoning_by_preset",
    ):
        if key not in policy:
            raise ModelResolveError(f"policy missing {key!r}")
        section = policy[key]
        if not isinstance(section, dict) or len(section) == 0:
            raise ModelResolveError(f"policy {key!r} must be a non-empty mapping")

    profiles = policy["profiles"]
    for role_key, hp_name in profiles.items():
        if not isinstance(role_key, str) or not role_key.strip():
            raise ModelResolveError("profiles keys must be non-empty strings")
        if not isinstance(hp_name, str) or not hp_name.strip():
            raise ModelResolveError(f"profiles[{role_key!r}] must be a non-empty string")

    for section_name in ("stage_defaults", "action_overrides"):
        section = policy[section_name]
        for entry_key, role in section.items():
            if not isinstance(entry_key, str) or not entry_key.strip():
                raise ModelResolveError(f"{section_name} keys must be non-empty strings")
            if not isinstance(role, str) or not role.strip():
                raise ModelResolveError(f"{section_name}[{entry_key!r}] must be a non-empty role")
            if role.strip() not in profiles:
                raise ModelResolveError(
                    f"{section_name}[{entry_key!r}] → role {role.strip()!r} not in profiles"
                )

    overrides = policy.get("action_reasoning_overrides")
    if overrides is not None and not isinstance(overrides, dict):
        raise ModelResolveError("action_reasoning_overrides must be a mapping when present")

    stage_actions = policy.get("stage_actions")
    if isinstance(stage_actions, dict):
        action_overrides = policy["action_overrides"]
        for usage_id, mapped_action in stage_actions.items():
            if not isinstance(mapped_action, str) or not mapped_action.strip():
                raise ModelResolveError(f"empty stage_actions[{usage_id!r}]")
            if mapped_action.strip() not in action_overrides:
                raise ModelResolveError(
                    f"stage_actions[{usage_id!r}] → {mapped_action!r} "
                    "is not an action_overrides key"
                )

    return policy


def _role_to_profile(policy: dict[str, Any], role: str) -> str:
    profiles = policy["profiles"]
    if role not in profiles:
        raise ModelResolveError(f"role {role!r} not in profiles")
    hp = profiles[role]
    if not isinstance(hp, str) or not hp.strip():
        raise ModelResolveError(f"invalid Hermes profile for role {role!r}")
    return hp.strip()


def _resolve_action(policy: dict[str, Any], action: str) -> tuple[str, str, str]:
    act = action.strip()
    action_overrides = policy["action_overrides"]
    if act not in action_overrides:
        raise ModelResolveError(f"unknown action {act!r}")
    role = action_overrides[act]
    if not isinstance(role, str) or not role.strip():
        raise ModelResolveError(f"empty role for action {act!r}")
    role = role.strip()
    return ("action", role, _role_to_profile(policy, role))


def _resolve_stage_key(policy: dict[str, Any], stage_key: str) -> tuple[str, str, str]:
    stage_defaults = policy["stage_defaults"]
    if stage_key not in stage_defaults:
        raise ModelResolveError(f"unknown stage key {stage_key!r}")
    role = stage_defaults[stage_key]
    if not isinstance(role, str) or not role.strip():
        raise ModelResolveError(f"empty role for stage {stage_key!r}")
    role = role.strip()
    return ("stage", role, _role_to_profile(policy, role))


def get_review_depth_preset(state: dict[str, Any], task_dir: Path | None = None) -> str:
    raw = state.get("review_depth_preset")
    if isinstance(raw, str):
        stripped = raw.strip()
        if stripped in ("light", "standard", "deep"):
            return stripped

    if task_dir is not None:
        inferred = _infer_preset_from_plan(task_dir, state)
        if inferred:
            return inferred

    return "standard"


def _infer_preset_from_plan(task_dir: Path, state: dict[str, Any]) -> str | None:
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    plan_name = artifacts.get("plan")
    if not isinstance(plan_name, str) or not plan_name.strip():
        return None
    plan_path = task_dir / plan_name.strip()
    if not plan_path.is_file():
        return None
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(
        r"\*\*Selected review-depth preset\*\*\s*\|\s*`(light|standard|deep)`",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).lower()
    m = re.search(
        r"Selected review-depth preset[^\n]*\b(light|standard|deep)\b",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).lower()
    return None


def get_reasoning_effort(
    policy: dict[str, Any],
    *,
    preset: str,
    role: str,
    action: str | None = None,
) -> str:
    overrides = policy.get("action_reasoning_overrides") or {}
    if action and isinstance(overrides.get(preset), dict):
        act_map = overrides[preset]
        if action in act_map and isinstance(act_map[action], str):
            return act_map[action].strip()
    by_preset = policy["reasoning_by_preset"]
    preset_map = by_preset.get(preset)
    if isinstance(preset_map, dict) and role in preset_map:
        val = preset_map[role]
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "medium"


def resolve_model(
    policy: dict[str, Any],
    *,
    state: dict[str, Any],
    task_dir: Path | None = None,
    action: str | None = None,
    stage_id: str | None = None,
    current_stage: str | None = None,
) -> dict[str, Any]:
    """Resolve logical role, Hermes profile, preset, and reasoning for a task boundary."""
    preset = get_review_depth_preset(state, task_dir)
    stage_display = (current_stage or "").strip() or None
    stage_id_norm = (stage_id or "").strip() or None
    action_arg = (action or "").strip() or None

    resolution_source = ""
    role = ""
    hermes_profile = ""
    resolved_action: str | None = None
    resolved_stage_key: str | None = None

    if action_arg:
        resolution_source, role, hermes_profile = _resolve_action(policy, action_arg)
        resolved_action = action_arg
    elif stage_id_norm:
        stage_actions = policy["stage_actions"]
        if stage_id_norm not in stage_actions:
            raise ModelResolveError(
                f"unknown usage stage id {stage_id_norm!r} (expected stage_actions key)"
            )
        mapped = stage_actions[stage_id_norm]
        if not isinstance(mapped, str) or not mapped.strip():
            raise ModelResolveError(f"empty stage_actions[{stage_id_norm!r}]")
        mapped = mapped.strip()
        if mapped not in policy["action_overrides"]:
            raise ModelResolveError(
                f"stage_actions[{stage_id_norm!r}] → {mapped!r} is not an action_overrides key"
            )
        resolution_source, role, hermes_profile = _resolve_action(policy, mapped)
        resolved_action = mapped
    else:
        if not stage_display:
            raise ModelResolveError(
                "no --action/--stage-id and current_stage is empty in state.yaml"
            )
        if stage_display not in policy["stage_defaults"]:
            raise ModelResolveError(
                f"unknown current_stage for stage_defaults: {stage_display!r}"
            )
        resolved_stage_key = stage_display
        resolution_source, role, hermes_profile = _resolve_stage_key(policy, stage_display)

    reasoning_expected = get_reasoning_effort(
        policy, preset=preset, role=role, action=resolved_action
    )

    last_profile = state.get("last_hermes_profile")
    if isinstance(last_profile, str):
        last_profile = last_profile.strip() or None
    else:
        last_profile = None

    profile_changed = bool(last_profile and last_profile != hermes_profile)
    usage_review_boundary = bool(
        stage_id_norm
        and (
            stage_id_norm.endswith("_review")
            or stage_id_norm in ("final_review", "final_summary")
        )
    )
    context_reset_recommended = bool(
        not profile_changed
        and last_profile
        and last_profile == hermes_profile
        and (usage_review_boundary or stage_display in ("spec", "plan"))
    )

    return {
        "resolution_source": resolution_source,
        "role": role,
        "hermes_profile": hermes_profile,
        "stage": stage_display,
        "stage_id": stage_id_norm or stage_display,
        "resolved_stage_key": resolved_stage_key,
        "action": resolved_action,
        "review_depth_preset": preset,
        "reasoning_expected": reasoning_expected,
        "reasoning_source": "policy_expected",
        "profile_changed": profile_changed,
        "last_hermes_profile": last_profile,
        "handoff_required": profile_changed,
        "last_profile_unknown": last_profile is None,
        "context_reset_recommended": context_reset_recommended,
    }


def resolve_for_task(
    task_dir: Path,
    *,
    policy_path: Path | None = None,
    action: str | None = None,
    stage_id: str | None = None,
) -> dict[str, Any]:
    policy = validate_policy(load_yaml(policy_path or default_policy_path()))
    state = load_task_state(task_dir)
    current_stage = state.get("current_stage")
    if current_stage is not None and not isinstance(current_stage, str):
        raise ModelResolveError("state.yaml current_stage must be a string")
    result = resolve_model(
        policy,
        state=state,
        task_dir=task_dir,
        action=action,
        stage_id=stage_id,
        current_stage=current_stage,
    )
    result["task_dir"] = str(task_dir.resolve())
    return result
