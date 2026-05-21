#!/usr/bin/env python3
"""Start a v4 dev-process job (open). Session is attached at job close (J1, J6)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from dp_cli_common import add_task_dir_arg
from job_roles import default_stage_id, profile_for_role
from jobs_store import JobsStoreError, is_v4_task, open_job, update_state_current_job


def _hermes_exe() -> str:
    return os.environ.get("HERMES_EXE", "hermes")


def _probe_profile(hermes: str, profile_name: str) -> None:
    try:
        r = subprocess.run(
            [hermes, f"--profile={profile_name}", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        print(
            f"dp_job_start.py: failed to run Hermes executable {hermes!r}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    if r.returncode != 0:
        print(
            f"dp_job_start.py: probe failed: `hermes --profile={profile_name} version` "
            f"(exit {r.returncode}). Start the job session with this profile only.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_task_dir_arg(parser)
    parser.add_argument("--role", required=True, help="Job role (spec, plan, review_worker, …)")
    parser.add_argument(
        "--handoff-in",
        action="append",
        default=[],
        metavar="PATH",
        help="Handoff briefing file(s) for J4 (repeatable; required except spec)",
    )
    parser.add_argument("--stage-id", default=None, help="Usage stage id for primary roles")
    parser.add_argument("--reviewer", default=None)
    parser.add_argument("--review-target", default=None)
    parser.add_argument("--review-round", type=int, default=None)
    parser.add_argument(
        "--no-probe-profile",
        action="store_true",
        help="Skip hermes --profile=<expected> version probe",
    )
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    task_dir = Path(args.task_dir).resolve()
    if not is_v4_task(task_dir):
        print(
            "dp_job_start.py: jobs.yaml not found — initialize with run-dp task start",
            file=sys.stderr,
        )
        return 2

    role = args.role.strip()
    stage_id = args.stage_id.strip() if args.stage_id else default_stage_id(role)
    expected_profile = profile_for_role(role)

    skip_probe = args.no_probe_profile or os.environ.get(
        "DEV_PROCESS_NO_PROFILE_PROBE", ""
    ).strip().lower() in ("1", "true", "yes")
    if not skip_probe:
        _probe_profile(_hermes_exe(), expected_profile)

    try:
        job = open_job(
            task_dir,
            role=role,
            handoff_in=args.handoff_in or None,
            reviewer=args.reviewer,
            review_target=args.review_target,
            review_round=args.review_round,
            stage_id=stage_id,
        )
        update_state_current_job(task_dir, job["id"])
    except JobsStoreError as exc:
        print(f"dp_job_start.py: {exc}", file=sys.stderr)
        return 2

    launch_cmd = f"hermes --profile={expected_profile} chat"
    out = {
        "job_id": job["id"],
        "role": role,
        "expected_profile": expected_profile,
        "profile": expected_profile,
        "handoff_in": job.get("handoff_in"),
        "handoff_out": job.get("handoff_out"),
        "stage_id": stage_id,
        "hermes_launch": launch_cmd,
        "next_steps": [
            launch_cmd,
            f"write briefing to {job.get('handoff_out')} before job close",
            "hermes sessions export … then run-dp job close --session-export …",
        ],
    }
    if args.print_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(out, ensure_ascii=False))
    print(
        "dp_job_start.py: does not launch an interactive Hermes session; run hermes_launch above.",
        file=sys.stderr,
    )
    print(
        "dp_job_start.py: job close checks export profile against expected_profile when observable.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
