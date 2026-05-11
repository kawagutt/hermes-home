#!/usr/bin/env python3
"""Resolve a Hermes profile from dev-process model_policy.yaml and optionally run hermes.

- Does not modify global Hermes configuration.
- Unless --record-state is passed, does not write state.yaml.
- Pass-through to Hermes: use `--` then hermes arguments, e.g.
    python3 dp_hermes.py --task-dir .hermes/tasks/T --action write_tests -- chat -q "hi"
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:  # pragma: no cover
    print("dp_hermes.py: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2) from e


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _default_policy_path() -> Path:
    return _script_dir().parent / "config" / "model_policy.yaml"


def _split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1 :]
    return argv, []


def _load_yaml(path: Path) -> Any:
    if not path.is_file():
        print(f"dp_hermes.py: policy file not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _validate_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict):
        print("dp_hermes.py: policy root must be a mapping", file=sys.stderr)
        raise SystemExit(2)
    if "schema_version" not in policy:
        print("dp_hermes.py: policy missing schema_version", file=sys.stderr)
        raise SystemExit(2)
    sv = policy["schema_version"]
    if sv != 1:
        print(f"dp_hermes.py: unsupported schema_version (expected 1): {sv!r}", file=sys.stderr)
        raise SystemExit(2)
    for key in ("profiles", "stage_defaults", "action_overrides"):
        if key not in policy:
            print(f"dp_hermes.py: policy missing {key!r}", file=sys.stderr)
            raise SystemExit(2)
        if not isinstance(policy[key], dict) or len(policy[key]) == 0:
            print(f"dp_hermes.py: policy {key!r} must be a non-empty mapping", file=sys.stderr)
            raise SystemExit(2)

    profiles = policy["profiles"]
    for role_key, hp_name in profiles.items():
        if not isinstance(role_key, str) or role_key.strip() == "":
            print("dp_hermes.py: profiles keys must be non-empty strings", file=sys.stderr)
            raise SystemExit(2)
        if not isinstance(hp_name, str) or hp_name.strip() == "":
            print(
                f"dp_hermes.py: profiles[{role_key!r}] must be a non-empty Hermes profile name string",
                file=sys.stderr,
            )
            raise SystemExit(2)

    for section_name in ("stage_defaults", "action_overrides"):
        section = policy[section_name]
        for entry_key, role in section.items():
            if not isinstance(entry_key, str) or entry_key.strip() == "":
                print(
                    f"dp_hermes.py: {section_name} keys must be non-empty strings",
                    file=sys.stderr,
                )
                raise SystemExit(2)
            if not isinstance(role, str) or role.strip() == "":
                print(
                    f"dp_hermes.py: {section_name}[{entry_key!r}] must be a non-empty role name",
                    file=sys.stderr,
                )
                raise SystemExit(2)
            if role.strip() not in profiles:
                print(
                    f"dp_hermes.py: {section_name}[{entry_key!r}] → role {role.strip()!r} "
                    f"not found in profiles",
                    file=sys.stderr,
                )
                raise SystemExit(2)
    return policy


def _load_task_state(task_dir: Path) -> dict[str, Any]:
    state_path = task_dir / "state.yaml"
    if not state_path.is_file():
        print(f"dp_hermes.py: state.yaml not found: {state_path}", file=sys.stderr)
        raise SystemExit(2)
    with state_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        print("dp_hermes.py: state.yaml root must be a mapping", file=sys.stderr)
        raise SystemExit(2)
    return data


def _hermes_exe() -> str:
    return os.environ.get("HERMES_EXE", "hermes")


def _probe_resolved_profile(hermes: str, profile_name: str) -> None:
    """Before launching Hermes, verify CLI accepts --profile and the profile works for one command."""
    try:
        r = subprocess.run(
            [hermes, f"--profile={profile_name}", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        print(
            f"dp_hermes.py: failed to run Hermes executable {hermes!r}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    if r.returncode != 0:
        print(
            f"dp_hermes.py: probe failed: `hermes --profile={profile_name} version` "
            f"(exit {r.returncode}). Check that the profile exists and Hermes supports --profile.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _resolve(
    policy: dict[str, Any],
    *,
    action: str | None,
    current_stage: str | None,
) -> tuple[str, str, str, str]:
    """Returns (resolution_source, role, hermes_profile, stage_for_display)."""
    profiles = policy["profiles"]
    stage_defaults = policy["stage_defaults"]
    action_overrides = policy["action_overrides"]

    stage_display = (current_stage or "").strip()

    if action is not None and action != "":
        act = action.strip()
        if act not in action_overrides:
            print(f"dp_hermes.py: unknown --action {act!r}", file=sys.stderr)
            raise SystemExit(2)
        role = action_overrides[act]
        if not isinstance(role, str) or role.strip() == "":
            print(f"dp_hermes.py: empty role for action {act!r}", file=sys.stderr)
            raise SystemExit(2)
        role = role.strip()
        if role not in profiles:
            print(f"dp_hermes.py: role {role!r} not in profiles", file=sys.stderr)
            raise SystemExit(2)
        hp = profiles[role]
        if not isinstance(hp, str) or hp.strip() == "":
            print(f"dp_hermes.py: invalid Hermes profile for role {role!r}", file=sys.stderr)
            raise SystemExit(2)
        return ("action", role, hp.strip(), stage_display)

    # Stage path
    if not stage_display:
        print(
            "dp_hermes.py: no --action and current_stage is empty in state.yaml",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if stage_display not in stage_defaults:
        print(
            f"dp_hermes.py: unknown current_stage for stage_defaults: {stage_display!r}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    role = stage_defaults[stage_display]
    if not isinstance(role, str) or role.strip() == "":
        print(f"dp_hermes.py: empty role for stage {stage_display!r}", file=sys.stderr)
        raise SystemExit(2)
    role = role.strip()
    if role not in profiles:
        print(f"dp_hermes.py: role {role!r} not in profiles", file=sys.stderr)
        raise SystemExit(2)
    hp = profiles[role]
    if not isinstance(hp, str) or hp.strip() == "":
        print(f"dp_hermes.py: invalid Hermes profile for role {role!r}", file=sys.stderr)
        raise SystemExit(2)
    return ("stage", role, hp.strip(), stage_display)


def _record_state(
    task_dir: Path,
    *,
    hermes_profile: str,
    action: str | None,
    resolution_source: str,
) -> None:
    state_path = task_dir / "state.yaml"
    data = _load_task_state(task_dir)
    data["last_hermes_profile"] = hermes_profile
    data["last_dev_process_action"] = action if action is not None else ""
    data["last_resolution_source"] = resolution_source
    with state_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)


def main() -> None:
    wrapper_argv, hermes_argv = _split_argv(sys.argv[1:])

    parser = argparse.ArgumentParser(prog="dp_hermes.py")
    parser.add_argument(
        "--task-dir",
        required=True,
        help="Path to .hermes/tasks/<task-id> (directory containing state.yaml).",
    )
    parser.add_argument(
        "--action",
        default=None,
        help="dev-process action id (see model_policy.yaml action_overrides).",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to model_policy.yaml (default: skills/dev-process/config/model_policy.yaml next to repo layout).",
    )
    parser.add_argument(
        "--print-profile-only",
        action="store_true",
        help="Print only the resolved Hermes profile name on stdout.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print only a JSON object on stdout.",
    )
    parser.add_argument(
        "--record-state",
        action="store_true",
        help="Update state.yaml last_* fields after Hermes exits 0 (default: never write state).",
    )

    args = parser.parse_args(wrapper_argv)

    if args.print_profile_only and args.print_json:
        print("dp_hermes.py: use only one of --print-profile-only and --print-json", file=sys.stderr)
        raise SystemExit(2)

    task_dir = Path(args.task_dir).resolve()
    policy_path = Path(args.policy).resolve() if args.policy else _default_policy_path()

    policy = _validate_policy(_load_yaml(policy_path))
    state = _load_task_state(task_dir)
    current_stage = state.get("current_stage")
    if current_stage is not None and not isinstance(current_stage, str):
        print("dp_hermes.py: state.yaml current_stage must be a string", file=sys.stderr)
        raise SystemExit(2)

    action_arg = args.action.strip() if args.action else None
    if action_arg == "":
        print("dp_hermes.py: empty --action is invalid", file=sys.stderr)
        raise SystemExit(2)

    resolution_source, role, hermes_profile, stage_display = _resolve(
        policy,
        action=action_arg,
        current_stage=current_stage,
    )

    hermes = _hermes_exe()
    task_dir_str = str(task_dir)
    json_action = action_arg if action_arg is not None else None

    # Dry-run modes: policy resolution only — no Hermes subprocess probes (CI / policy checks).
    if args.print_profile_only:
        print(hermes_profile, flush=True)
        return

    if args.print_json:
        payload = {
            "task_dir": task_dir_str,
            "stage": stage_display or None,
            "action": json_action,
            "resolution_source": resolution_source,
            "role": role,
            "hermes_profile": hermes_profile,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", end="", flush=True)
        return

    # Normal launch: verify resolved profile works with Hermes before printing model line or running user command.
    _probe_resolved_profile(hermes, hermes_profile)

    mu_action = json_action if json_action is not None else "none"
    print(
        f"Model usage: stage={stage_display or 'none'}, action={mu_action}, "
        f"role={role}, hermes_profile={hermes_profile}",
        flush=True,
    )
    cmd = [hermes, f"--profile={hermes_profile}", *hermes_argv]
    try:
        r = subprocess.run(cmd)
    except OSError as exc:
        print(
            f"dp_hermes.py: failed to run Hermes executable {hermes!r}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    if args.record_state and r.returncode == 0:
        _record_state(
            task_dir,
            hermes_profile=hermes_profile,
            action=action_arg,
            resolution_source=resolution_source,
        )
    raise SystemExit(r.returncode)


if __name__ == "__main__":
    main()
