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

from model_resolve import (
    ModelResolveError,
    default_policy_path,
    load_task_state,
    load_yaml,
    resolve_for_task,
    validate_policy,
)


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1 :]
    return argv, []


def _hermes_exe() -> str:
    return os.environ.get("HERMES_EXE", "hermes")


def _probe_resolved_profile(hermes: str, profile_name: str) -> None:
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


def _record_state(
    task_dir: Path,
    *,
    hermes_profile: str,
    action: str | None,
    resolution_source: str,
    stage_id: str | None,
) -> None:
    state_path = task_dir / "state.yaml"
    data = load_task_state(task_dir)
    data["last_hermes_profile"] = hermes_profile
    data["last_dev_process_action"] = action if action is not None else ""
    data["last_resolution_source"] = resolution_source
    if stage_id:
        data["last_model_stage_id"] = stage_id
    with state_path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data, f, sort_keys=False, allow_unicode=True, default_flow_style=False
        )


def _exit_resolve_error(exc: ModelResolveError) -> None:
    print(f"dp_hermes.py: {exc}", file=sys.stderr)
    raise SystemExit(2)


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
        "--stage-id",
        default=None,
        help="usage stage id for artifacts.model_usage (stage_actions key; when --action omitted).",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to model_policy.yaml (default: skills/dev-process/config/model_policy.yaml).",
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
        print(
            "dp_hermes.py: use only one of --print-profile-only and --print-json",
            file=sys.stderr,
        )
        raise SystemExit(2)

    task_dir = Path(args.task_dir).resolve()
    policy_path = Path(args.policy).resolve() if args.policy else default_policy_path()

    action_arg = args.action.strip() if args.action else None
    if action_arg == "":
        print("dp_hermes.py: empty --action is invalid", file=sys.stderr)
        raise SystemExit(2)
    stage_id_arg = args.stage_id.strip() if args.stage_id else None
    if stage_id_arg == "":
        print("dp_hermes.py: empty --stage-id is invalid", file=sys.stderr)
        raise SystemExit(2)

    try:
        resolved = resolve_for_task(
            task_dir,
            policy_path=policy_path,
            action=action_arg,
            stage_id=stage_id_arg if not action_arg else None,
        )
    except ModelResolveError as exc:
        _exit_resolve_error(exc)

    hermes_profile = resolved["hermes_profile"]
    hermes = _hermes_exe()

    if args.print_profile_only:
        print(hermes_profile, flush=True)
        return

    if args.print_json:
        print(json.dumps(resolved, ensure_ascii=False, indent=2) + "\n", end="", flush=True)
        return

    _probe_resolved_profile(hermes, hermes_profile)

    mu_action = resolved.get("action") or "none"
    stage_label = resolved.get("stage_id") or resolved.get("stage") or "none"
    print(
        f"Model usage: stage={stage_label}, action={mu_action}, "
        f"role={resolved['role']}, hermes_profile={hermes_profile}, "
        f"preset={resolved['review_depth_preset']}, "
        f"reasoning_expected={resolved['reasoning_expected']}"
        + (
            ", handoff_required=true"
            if resolved.get("handoff_required")
            else ", handoff_required=false"
        ),
        flush=True,
    )
    if resolved.get("handoff_required"):
        print(
            "Model handoff: start a new Hermes session with "
            f"`hermes --profile={hermes_profile}` (or re-run this script with `--`). "
            "Use --record-state to persist last_hermes_profile. "
            "Profiles do not switch mid-session.",
            file=sys.stderr,
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
            action=resolved.get("action"),
            resolution_source=resolved["resolution_source"],
            stage_id=stage_id_arg or resolved.get("stage_id"),
        )
    raise SystemExit(r.returncode)


# Backward-compatible aliases for tests and inline imports.
_validate_policy = validate_policy
_load_yaml = load_yaml


if __name__ == "__main__":
    main()
