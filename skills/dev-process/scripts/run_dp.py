#!/usr/bin/env python3
"""run-dp: v4 dev-process public API (task | job | render | validate)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from jobs_store import is_v4_task, looks_like_pre_v4_task


def _scripts_dir() -> Path:
    return Path(__file__).resolve().parent


def _python() -> str:
    return sys.executable


def _run(script: str, argv: list[str]) -> int:
    cmd = [_python(), str(_scripts_dir() / script), *argv]
    return subprocess.run(cmd).returncode


def _templates_dir() -> Path:
    return _scripts_dir().parent / "templates"


def cmd_task_start(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).resolve()

    env_code = _run("check_helper_env.py", [])
    if env_code != 0:
        return env_code

    task_dir.mkdir(parents=True, exist_ok=True)
    tid = task_dir.name

    if looks_like_pre_v4_task(task_dir) and not args.force_new_v4:
        print(
            "run-dp task start: task looks pre-v4 (state.yaml without jobs.yaml). "
            "Refusing to add jobs.yaml. Use a new task directory or --force-new-v4 "
            "only when intentionally migrating (do not use on completed historical tasks).",
            file=sys.stderr,
        )
        return 2

    jobs_tpl = _templates_dir() / "jobs.yaml"
    state_tpl = _templates_dir() / "state.yaml"
    jobs_dst = task_dir / "jobs.yaml"
    state_dst = task_dir / "state.yaml"

    if not jobs_dst.is_file() and jobs_tpl.is_file():
        text = jobs_tpl.read_text(encoding="utf-8").replace('task_id: ""', f"task_id: {tid}")
        jobs_dst.write_text(text, encoding="utf-8")
    if not state_dst.is_file() and state_tpl.is_file():
        text = state_tpl.read_text(encoding="utf-8").replace('task_id: ""', f"task_id: {tid}")
        state_dst.write_text(text, encoding="utf-8")

    (task_dir / "handoffs").mkdir(parents=True, exist_ok=True)
    (task_dir / "generated").mkdir(parents=True, exist_ok=True)

    print(f"task start OK: {task_dir}")
    return 0


def cmd_job_start(args: argparse.Namespace) -> int:
    argv = ["--task-dir", args.task_dir, "--role", args.role]
    for hin in args.handoff_in or []:
        argv.extend(["--handoff-in", hin])
    if args.stage_id:
        argv.extend(["--stage-id", args.stage_id])
    if args.reviewer:
        argv.extend(["--reviewer", args.reviewer])
    if args.review_target:
        argv.extend(["--review-target", args.review_target])
    if args.review_round is not None:
        argv.extend(["--review-round", str(args.review_round)])
    if args.print_json:
        argv.append("--print-json")
    return _run("dp_job_start.py", argv)


def cmd_job_close(args: argparse.Namespace) -> int:
    argv = [
        "--task-dir",
        args.task_dir,
        "--session-export",
        args.session_export,
    ]
    if args.session_id:
        argv.extend(["--session-id", args.session_id])
    if args.job_id:
        argv.extend(["--job-id", args.job_id])
    for ao in args.artifacts_out or []:
        argv.extend(["--artifacts-out", ao])
    code = _run("dp_job_close.py", argv)
    if code != 0:
        return code
    r1 = _run("render_jobs.py", ["model-usage", "--task-dir", args.task_dir])
    r2 = _run("render_jobs.py", ["review-summary", "--task-dir", args.task_dir])
    return r1 if r1 != 0 else r2


def cmd_render(args: argparse.Namespace) -> int:
    return _run("render_jobs.py", [args.kind, "--task-dir", args.task_dir])


def cmd_validate(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).resolve()
    argv = [str(task_dir)]
    if args.strict:
        argv.append("--strict")
    v4 = _run("validate_jobs_v4.py", argv)
    if v4 != 0:
        return v4
    if not is_v4_task(task_dir):
        return 0
    st = _run("validate_state.py", [args.task_dir])
    if st != 0 and args.strict:
        return st
    return 0 if v4 == 0 and st == 0 else max(v4, st)


def main() -> int:
    parser = argparse.ArgumentParser(prog="run-dp", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_task = sub.add_parser("task", help="Task lifecycle")
    p_task_sub = p_task.add_subparsers(dest="task_cmd", required=True)
    p_ts = p_task_sub.add_parser("start")
    p_ts.add_argument("--task-dir", required=True)
    p_ts.add_argument(
        "--force-new-v4",
        action="store_true",
        help="Allow adding jobs.yaml to a directory that already has state.yaml (migration only)",
    )
    p_ts.set_defaults(func=cmd_task_start)

    p_job = sub.add_parser("job", help="Job lifecycle (v4)")
    p_job_sub = p_job.add_subparsers(dest="job_cmd", required=True)
    p_js = p_job_sub.add_parser("start")
    p_js.add_argument("--task-dir", required=True)
    p_js.add_argument("--role", required=True)
    p_js.add_argument(
        "--handoff-in",
        action="append",
        default=[],
        help="Handoff briefing path(s); repeat for review_synthesis",
    )
    p_js.add_argument("--stage-id", default=None)
    p_js.add_argument("--reviewer", default=None)
    p_js.add_argument("--review-target", default=None)
    p_js.add_argument("--review-round", type=int, default=None)
    p_js.add_argument("--print-json", action="store_true")
    p_js.set_defaults(func=cmd_job_start)

    p_jc = p_job_sub.add_parser("close")
    p_jc.add_argument("--task-dir", required=True)
    p_jc.add_argument(
        "--session-id",
        default=None,
        help="Session id (default: from export JSON)",
    )
    p_jc.add_argument("--session-export", required=True)
    p_jc.add_argument("--job-id", default=None)
    p_jc.add_argument("--artifacts-out", action="append", default=[])
    p_jc.set_defaults(func=cmd_job_close)

    p_render = sub.add_parser("render", help="Render display artifacts from jobs.yaml")
    p_render.add_argument("kind", choices=("model-usage", "review-summary"))
    p_render.add_argument("--task-dir", required=True)
    p_render.set_defaults(func=cmd_render)

    p_val = sub.add_parser("validate", help="Validate task (v4 + state)")
    p_val.add_argument("--task-dir", required=True)
    p_val.add_argument("--strict", action="store_true")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
