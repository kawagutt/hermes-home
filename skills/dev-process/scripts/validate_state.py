#!/usr/bin/env python3
"""Validate a dev-process task state.yaml with deterministic local checks."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

LATEST_RE = re.compile(r"^reviews/(?P<stage>[^/]+)/round_(?P<num>\d{2,})/synthesis\.md$")
NUMBERED_TASK_ROOT_MD_RE = re.compile(r"^\d{4}_[^/]+\.md$")


def load_state(task: Path) -> dict:
    state_path = task / "state.yaml"
    if not state_path.exists():
        raise SystemExit(f"ERROR missing state.yaml: {state_path}")
    with state_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def is_task_root_markdown(rel: str) -> bool:
    path = Path(rel)
    return len(path.parts) == 1 and path.suffix == ".md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Path to .hermes/tasks/<task-id>")
    args = parser.parse_args()
    task = Path(args.task)
    state = load_state(task)
    errors: list[str] = []

    if state.get("task_id") != task.name:
        errors.append(f"task_id mismatch: state={state.get('task_id')!r} dir={task.name!r}")

    artifacts = state.get("artifacts") or {}
    task_root_markdown_files = {p.name for p in task.glob("*.md")}
    numbered_root_markdown_files = {name for name in task_root_markdown_files if NUMBERED_TASK_ROOT_MD_RE.match(name)}
    for name in task_root_markdown_files:
        if not NUMBERED_TASK_ROOT_MD_RE.match(name):
            errors.append(f"task-root markdown is not numbered NNNN_<stem>.md: {name}")
    for key, rel in artifacts.items():
        if not rel:
            continue
        artifact_path = task / rel
        if not artifact_path.exists():
            errors.append(f"missing artifact {key}: {rel}")
            continue
        if is_task_root_markdown(rel) and not NUMBERED_TASK_ROOT_MD_RE.match(rel):
            errors.append(f"artifact {key} is task-root markdown but not numbered NNNN_<stem>.md: {rel}")
    for name in numbered_root_markdown_files:
        if name not in {rel for rel in artifacts.values() if rel}:
            # Numbered task-root files may be historical versions, so this is allowed.
            continue

    rounds = state.get("review_rounds") or {}
    latest = state.get("latest_reviews") or {}
    for stage, rel in latest.items():
        count = int(rounds.get(stage, 0) or 0)
        if count and not rel:
            errors.append(f"latest review missing for {stage} with review_rounds={count}")
            continue
        if not count and rel:
            errors.append(f"latest review set for {stage} while review_rounds=0: {rel}")
        if not rel:
            continue
        match = LATEST_RE.match(rel)
        if not match:
            errors.append(f"latest review path has invalid format for {stage}: {rel}")
        else:
            path_stage = match.group("stage")
            path_num = int(match.group("num"))
            if path_stage != stage:
                errors.append(f"latest review stage mismatch: key={stage} path={rel}")
            if count and path_num != count:
                errors.append(f"latest review round mismatch for {stage}: review_rounds={count} path={rel}")
        if rel and not (task / rel).exists():
            errors.append(f"missing latest review {stage}: {rel}")

    branch = state.get("branch") or {}
    required_branch = [
        "name",
        "feasibility_checked_before_human_spec_gate",
        "task_branch_precondition_met",
        "commits_allowed_on_task_branch",
        "task_artifacts_commit_by_default",
    ]
    for key in required_branch:
        if key not in branch:
            errors.append(f"missing branch field: {key}")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print(f"OK {task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
