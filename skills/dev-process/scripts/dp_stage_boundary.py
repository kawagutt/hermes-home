#!/usr/bin/env python3
"""Stage-boundary profile resolution and model_usage row generation.

A. Completed stage usage row: --print-markdown-row + --session-export (no handoff message).
B. Next segment launch: --print-json for --stage-id of the stage you are about to start.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from model_resolve import ModelResolveError, default_policy_path, resolve_for_task
from session_usage import _load_session, build_summary, markdown_row, resolve_time_cell


def main() -> int:
    parser = argparse.ArgumentParser(prog="dp_stage_boundary.py")
    parser.add_argument("--task-dir", required=True, help="Path to .hermes/tasks/<task-id>")
    parser.add_argument(
        "--stage-id",
        required=True,
        help="artifacts.model_usage stage id (stage_actions key)",
    )
    parser.add_argument("--action", default=None, help="Optional action override")
    parser.add_argument("--policy", default=None, help="Path to model_policy.yaml")
    parser.add_argument(
        "--session-export",
        default=None,
        help="Path to hermes sessions export JSONL for the ending session",
    )
    parser.add_argument(
        "--dev-action",
        default="",
        help="Human-readable action label for the usage row",
    )
    parser.add_argument(
        "--print-markdown-row",
        action="store_true",
        help="Print a compact model_usage Markdown row (requires --session-export)",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print resolution JSON (default when not printing a row)",
    )
    args = parser.parse_args()

    policy_path = Path(args.policy).resolve() if args.policy else default_policy_path()
    task_dir = Path(args.task_dir).resolve()
    stage_id = args.stage_id.strip()
    if not stage_id:
        print("dp_stage_boundary.py: empty --stage-id", file=sys.stderr)
        return 2

    try:
        resolved = resolve_for_task(
            task_dir,
            policy_path=policy_path,
            action=args.action.strip() if args.action else None,
            stage_id=stage_id,
        )
    except ModelResolveError as exc:
        print(f"dp_stage_boundary.py: {exc}", file=sys.stderr)
        return 2

    if args.print_markdown_row:
        if not args.session_export:
            print(
                "dp_stage_boundary.py: --print-markdown-row requires --session-export",
                file=sys.stderr,
            )
            return 2
        try:
            summary = build_summary(_load_session(Path(args.session_export)))
        except (OSError, ValueError) as exc:
            print(f"dp_stage_boundary.py: invalid session export: {exc}", file=sys.stderr)
            return 2
        dev_action = args.dev_action.strip() or resolved.get("action") or stage_id
        reasoning = f"expected {resolved['reasoning_expected']} / observed unknown"
        print(
            markdown_row(
                summary,
                time_cell=resolve_time_cell("auto", summary),
                stage_id=stage_id,
                action=dev_action,
                profile=resolved["hermes_profile"],
                role=resolved["role"],
                preset=resolved["review_depth_preset"],
                reasoning=reasoning,
                evidence=f"hermes sessions export --session-id {summary.get('session_id', '<id>')}",
            )
        )
        return 0

    print(json.dumps(resolved, ensure_ascii=False, indent=2))
    if resolved.get("handoff_required"):
        print(
            f"Model handoff: hermes --profile={resolved['hermes_profile']} "
            f"(or dp_hermes.py --record-state …)",
            file=sys.stderr,
        )
    elif resolved.get("last_profile_unknown"):
        print(
            "Note: last_hermes_profile unset; use dp_hermes.py --record-state after launch.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
