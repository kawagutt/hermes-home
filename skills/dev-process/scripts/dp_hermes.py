#!/usr/bin/env python3
"""Resolve a Hermes profile from dev-process model_policy.yaml and optionally run hermes.

- Does not modify global Hermes configuration.
- Unless --record-state is passed, does not write state.yaml.
- Pass-through to Hermes: use `--` then hermes arguments, e.g.
    python3 dp_hermes.py --task-dir .hermes/tasks/T --action write_tests -- chat -q "hi"
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError as e:  # pragma: no cover
    print("dp_hermes.py: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2) from e

from dp_cli_common import (
    add_policy_arg,
    add_task_dir_arg,
    print_handoff_notes,
    print_resolution_json,
    resolve_policy_path,
    resolve_task_boundary,
)
from model_resolve import load_task_state, load_yaml, validate_policy


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
    updates = {
        "last_hermes_profile": hermes_profile,
        "last_dev_process_action": action if action is not None else "",
        "last_resolution_source": resolution_source,
    }
    if stage_id:
        updates["last_model_stage_id"] = stage_id
    try:
        from ruamel.yaml import YAML

        ry = YAML()
        ry.preserve_quotes = True
        with state_path.open(encoding="utf-8") as f:
            data = ry.load(f)
        if not isinstance(data, dict):
            raise ValueError("state.yaml root must be a mapping")
        data.update(updates)
        with state_path.open("w", encoding="utf-8") as f:
            ry.dump(data, f)
        return
    except ImportError:
        pass
    data = load_task_state(task_dir)
    data.update(updates)
    with state_path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data, f, sort_keys=False, allow_unicode=True, default_flow_style=False
        )


def main() -> None:
    wrapper_argv, hermes_argv = _split_argv(sys.argv[1:])

    parser = argparse.ArgumentParser(prog="dp_hermes.py")
    add_task_dir_arg(parser)
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
    add_policy_arg(parser)
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
    parser.add_argument(
        "--handoff-only",
        action="store_true",
        help="Resolve only: print JSON on stdout and exit 0 without launching Hermes.",
    )
    parser.add_argument(
        "--strict-launch",
        action="store_true",
        help="Fail when current_stage=implementation and neither --stage-id nor --action is set (default).",
    )

    args = parser.parse_args(wrapper_argv)

    if args.handoff_only and (args.print_profile_only or args.record_state):
        print(
            "dp_hermes.py: --handoff-only cannot be combined with --print-profile-only "
            "or --record-state",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if args.print_profile_only and args.print_json:
        print(
            "dp_hermes.py: use only one of --print-profile-only and --print-json",
            file=sys.stderr,
        )
        raise SystemExit(2)

    task_dir = Path(args.task_dir).resolve()
    action_arg = args.action.strip() if args.action else None
    if action_arg == "":
        print("dp_hermes.py: empty --action is invalid", file=sys.stderr)
        raise SystemExit(2)
    stage_id_arg = args.stage_id.strip() if args.stage_id else None
    if stage_id_arg == "":
        print("dp_hermes.py: empty --stage-id is invalid", file=sys.stderr)
        raise SystemExit(2)

    if args.record_state and action_arg and action_arg.startswith("review_"):
        print(
            "dp_hermes.py: --record-state must not be used with review worker actions "
            f"({action_arg!r}); review sessions are recorded in review_manifest.yaml only",
            file=sys.stderr,
        )
        raise SystemExit(2)

    def _env_truthy(name: str) -> bool:
        return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")

    enforce_strict_launch = True
    if not action_arg and not stage_id_arg:
        try:
            state = load_task_state(task_dir)
            current_stage = state.get("current_stage")
            if (
                isinstance(current_stage, str)
                and current_stage.strip() == "implementation"
            ):
                msg = (
                    "dp_hermes.py: current_stage=implementation with no --stage-id or "
                    "--action resolves to dp-code (implement). For primary phase work use "
                    "--stage-id implementation_phase_NN; for checkpoint reviewers use "
                    "--action review_<agent> (manifest only, not model_usage)."
                )
                if enforce_strict_launch:
                    print(msg, file=sys.stderr)
                    raise SystemExit(2)
                print(f"WARNING: {msg}", file=sys.stderr)
        except Exception as exc:
            if enforce_strict_launch:
                print(
                    f"dp_hermes.py: launch precheck failed: {exc}",
                    file=sys.stderr,
                )
                raise SystemExit(2) from exc

    resolved = resolve_task_boundary(
        "dp_hermes.py",
        task_dir=task_dir,
        policy_path=resolve_policy_path(args.policy),
        stage_id=stage_id_arg if not action_arg else None,
        action=action_arg,
    )

    hermes_profile = resolved["hermes_profile"]
    hermes = _hermes_exe()

    if args.handoff_only:
        print_resolution_json(resolved)
        print_handoff_notes("dp_hermes.py", resolved, handoff_only=True)
        return

    if args.print_profile_only:
        print(hermes_profile, flush=True)
        return

    if args.print_json:
        print_resolution_json(resolved)
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
        )
        + (
            ", session_reset_required=true"
            if resolved.get("session_reset_required")
            else ", session_reset_required=false"
        ),
        flush=True,
    )
    print_handoff_notes("dp_hermes.py", resolved)

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
