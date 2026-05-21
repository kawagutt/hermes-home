#!/usr/bin/env python3
"""Close a v4 dev-process job: record session export usage and handoff (J5, J6)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dp_cli_common import add_task_dir_arg
from jobs_store import JobsStoreError, close_job, is_v4_task, update_state_current_job
from session_profile import observed_profile_from_export
from session_usage import _load_session, build_summary


def _parse_artifacts_out(raw: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"expected key=path, got {item!r}")
        key, path = item.split("=", 1)
        key, path = key.strip(), path.strip()
        if not key or not path:
            raise ValueError(f"expected key=path, got {item!r}")
        out[key] = path
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_task_dir_arg(parser)
    parser.add_argument("--job-id", default=None, help="Open job id (default: current open job)")
    parser.add_argument(
        "--session-id",
        default=None,
        help="Hermes session id (default: id from --session-export)",
    )
    parser.add_argument(
        "--session-export",
        required=True,
        help="Path to hermes sessions export JSONL",
    )
    parser.add_argument(
        "--artifacts-out",
        action="append",
        default=[],
        metavar="KEY=PATH",
        help="Artifact produced by this job (repeatable)",
    )
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    task_dir = Path(args.task_dir).resolve()
    if not is_v4_task(task_dir):
        print("dp_job_close.py: jobs.yaml not found", file=sys.stderr)
        return 2

    try:
        payload = _load_session(Path(args.session_export))
        summary = build_summary(payload)
    except (OSError, ValueError) as exc:
        print(f"dp_job_close.py: invalid session export: {exc}", file=sys.stderr)
        return 2

    export_sid = str(summary.get("session_id") or "").strip()
    session_id = args.session_id.strip() if args.session_id else export_sid
    if not session_id:
        print("dp_job_close.py: no session id in export or --session-id", file=sys.stderr)
        return 2
    if export_sid and export_sid != session_id:
        print(
            f"dp_job_close.py: export session_id {export_sid!r} != --session-id {session_id!r}",
            file=sys.stderr,
        )
        return 2

    try:
        artifacts = _parse_artifacts_out(args.artifacts_out)
    except ValueError as exc:
        print(f"dp_job_close.py: {exc}", file=sys.stderr)
        return 2

    usage = {
        "input_tokens": summary.get("input_tokens"),
        "output_tokens": summary.get("output_tokens"),
        "reasoning_tokens": summary.get("reasoning_tokens"),
        "estimated_cost_usd": summary.get("estimated_cost_usd"),
        "actual_cost_usd": summary.get("actual_cost_usd"),
    }
    observed = observed_profile_from_export(payload, summary)

    try:
        job = close_job(
            task_dir,
            job_id=args.job_id,
            session_id=session_id,
            model=str(summary.get("model") or ""),
            artifacts_out=artifacts,
            usage=usage,
            observed_profile=observed,
        )
        update_state_current_job(task_dir, None)
    except JobsStoreError as exc:
        print(f"dp_job_close.py: {exc}", file=sys.stderr)
        return 2

    if args.print_json:
        print(json.dumps(job, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"closed {job['id']} session={job['session_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
