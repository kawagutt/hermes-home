"""Shared CLI helpers for dp_hermes.py and dp_stage_boundary.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from model_resolve import ModelResolveError, default_policy_path, resolve_for_task


def add_policy_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to model_policy.yaml (default: skills/dev-process/config/model_policy.yaml).",
    )


def add_task_dir_arg(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    parser.add_argument(
        "--task-dir",
        required=required,
        help="Path to .hermes/tasks/<task-id> (directory containing state.yaml).",
    )


def resolve_policy_path(policy_arg: str | None) -> Path:
    return Path(policy_arg).resolve() if policy_arg else default_policy_path()


def resolve_task_boundary(
    prog: str,
    *,
    task_dir: Path,
    policy_path: Path,
    stage_id: str | None,
    action: str | None,
) -> dict[str, Any]:
    stage_norm = stage_id.strip() if stage_id else None
    if stage_norm == "":
        print(f"{prog}: empty --stage-id", file=sys.stderr)
        raise SystemExit(2)
    action_norm = action.strip() if action else None
    if action_norm == "":
        print(f"{prog}: empty --action", file=sys.stderr)
        raise SystemExit(2)
    try:
        return resolve_for_task(
            task_dir,
            policy_path=policy_path,
            action=action_norm,
            stage_id=stage_norm,
        )
    except ModelResolveError as exc:
        print(f"{prog}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def print_resolution_json(resolved: dict[str, Any]) -> None:
    print(json.dumps(resolved, ensure_ascii=False, indent=2), end="\n", flush=True)


def print_handoff_notes(
    prog: str, resolved: dict[str, Any], *, handoff_only: bool = False
) -> None:
    profile = resolved.get("hermes_profile", "")
    if resolved.get("session_reset_required"):
        profile_note = (
            " Hermes profile also changes." if resolved.get("handoff_required") else ""
        )
        print(
            f"{prog}: session_reset_required=true — MUST start a new Hermes session "
            "for this primary segment (standard/deep: one row = one session). "
            "Continuing this session after the boundary is a process violation."
            f"{profile_note}",
            file=sys.stderr,
        )
    elif resolved.get("handoff_required"):
        if handoff_only:
            print(
                f"{prog}: handoff_required=true — Hermes profile changes; "
                "start a new session (do not continue this session).",
                file=sys.stderr,
            )
        else:
            print(
                f"{prog}: handoff_required=true — you MUST start a new Hermes session; "
                "continuing this session after a profile boundary is invalid. "
                "Use --handoff-only to resolve without launching, then "
                f"`hermes --profile={profile}` (or re-run with --record-state).",
                file=sys.stderr,
            )
    elif resolved.get("context_reset_recommended"):
        print(
            f"{prog}: context_reset_recommended=true — advisory only (light preset); "
            "SHOULD start a new Hermes session for this review round or long chain.",
            file=sys.stderr,
        )
    elif resolved.get("last_profile_unknown"):
        print(
            f"{prog}: last_hermes_profile unset; use dp_hermes.py --record-state after launch.",
            file=sys.stderr,
        )
