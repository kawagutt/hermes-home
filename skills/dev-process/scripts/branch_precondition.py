#!/usr/bin/env python3
"""Record dev-process task branch precondition evidence in state.yaml/timeline."""
from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path

import yaml


def load_state(task: Path) -> dict:
    with (task / "state.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_state(task: Path, state: dict) -> None:
    with (task / "state.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False, allow_unicode=True)


def current_git_branch(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Path to .hermes/tasks/<task-id>")
    parser.add_argument("branch", help="Dev-process task branch name")
    parser.add_argument("--dry-run", action="store_true", help="Show intended state/timeline updates")
    parser.add_argument("--apply", action="store_true", help="Apply state/timeline updates")
    parser.add_argument("--evidence", default="", help="Command/evidence used to create or switch branch")
    parser.add_argument("--repo", default=".", help="Repository path used to verify the current git branch")
    parser.add_argument("--skip-git-check", action="store_true", help="Skip current git branch verification, for isolated tests only")
    args = parser.parse_args()

    task = Path(args.task)
    repo = Path(args.repo)
    state = load_state(task)
    artifacts = state.setdefault("artifacts", {})
    timeline_rel = artifacts.get("timeline")
    if not timeline_rel:
        raise SystemExit("ERROR artifacts.timeline must be materialized before branch helper apply")
    timeline = task / timeline_rel
    if not timeline.exists():
        raise SystemExit(f"ERROR missing timeline artifact: {timeline_rel}")

    current = None if args.skip_git_check else current_git_branch(repo)
    if not args.skip_git_check and current != args.branch:
        print(f"ERROR current git branch {current!r} does not match expected task branch {args.branch!r}")
        return 1

    evidence = args.evidence or f"branch helper recorded branch {args.branch}"
    if args.dry_run or not args.apply:
        print("DRY-RUN branch precondition update")
        print(f"branch.name={args.branch}")
        print("branch.task_branch_precondition_met=true")
        print("branch.commits_allowed_on_task_branch=true")
        print(f"timeline += {evidence}")
        return 0

    branch = state.setdefault("branch", {})
    branch["name"] = args.branch
    branch["task_branch_precondition_met"] = True
    branch["commits_allowed_on_task_branch"] = True
    write_state(task, state)
    with timeline.open("a", encoding="utf-8") as f:
        f.write(
            f"| {date.today().isoformat()} | branch | "
            "Task branch precondition recorded | "
            f"Branch `{args.branch}`; evidence: `{evidence}`. |\n"
        )
    print(f"UPDATED branch precondition for {args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
