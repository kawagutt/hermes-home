#!/usr/bin/env python3
"""Validate a dev-process task state.yaml with deterministic local checks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

POLICY_PATH = Path(__file__).resolve().parent.parent / "config" / "model_policy.yaml"

LATEST_RE = re.compile(
    r"^reviews/(?P<stage>[^/]+)/round_(?P<num>\d{2,})/synthesis\.md$"
)
NUMBERED_TASK_ROOT_MD_RE = re.compile(r"^\d{4}_[^/]+\.md$")


def load_state(task: Path) -> dict:
    state_path = task / "state.yaml"
    if not state_path.exists():
        raise SystemExit(f"ERROR missing state.yaml: {state_path}")
    with state_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_policy() -> dict[str, Any]:
    if not POLICY_PATH.is_file():
        raise SystemExit(f"ERROR policy file not found: {POLICY_PATH}")
    with POLICY_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR policy root must be a mapping: {POLICY_PATH}")
    return data


def usage_only_stage_ids(policy: dict[str, Any]) -> set[str]:
    stage_actions = policy.get("stage_actions") or {}
    stage_defaults = policy.get("stage_defaults") or {}
    if not isinstance(stage_actions, dict) or not isinstance(stage_defaults, dict):
        return set()
    return set(stage_actions) - set(stage_defaults)


def is_task_root_markdown(rel: str) -> bool:
    path = Path(rel)
    return len(path.parts) == 1 and path.suffix == ".md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Path to .hermes/tasks/<task-id>")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (e.g. missing last_hermes_profile) as errors.",
    )
    args = parser.parse_args()
    task = Path(args.task)
    state = load_state(task)
    policy = load_policy()
    errors: list[str] = []
    warnings: list[str] = []

    current_stage = (state.get("current_stage") or "").strip()
    if current_stage:
        bad_usage = usage_only_stage_ids(policy)
        if current_stage in bad_usage:
            errors.append(
                f"current_stage {current_stage!r} is a usage stage id only "
                f"(stage_actions key, not a state stage). Use orchestrator stages "
                f"({', '.join(sorted((policy.get('stage_defaults') or {}).keys()))}) "
                f"in state.yaml; pass --stage-id {current_stage!r} to dp_hermes.py instead."
            )

    last_profile = state.get("last_hermes_profile")
    if not (isinstance(last_profile, str) and last_profile.strip()):
        warnings.append(
            "missing last_hermes_profile (run dp_hermes.py with --record-state after "
            "each profile boundary so handoff_required works)"
        )

    if state.get("task_id") != task.name:
        errors.append(
            f"task_id mismatch: state={state.get('task_id')!r} dir={task.name!r}"
        )

    artifacts = state.get("artifacts") or {}
    task_root_markdown_files = {p.name for p in task.glob("*.md")}
    numbered_root_markdown_files = {
        name
        for name in task_root_markdown_files
        if NUMBERED_TASK_ROOT_MD_RE.match(name)
    }
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
            errors.append(
                f"artifact {key} is task-root markdown but not numbered NNNN_<stem>.md: {rel}"
            )
    for name in numbered_root_markdown_files:
        if name not in {rel for rel in artifacts.values() if rel}:
            # Numbered task-root files may be historical versions, so this is allowed.
            continue

    rounds = state.get("review_rounds") or {}
    latest = state.get("latest_reviews") or {}
    for stage, rel in latest.items():
        count = int(rounds.get(stage, 0) or 0)
        if count and not rel:
            errors.append(
                f"latest review missing for {stage} with review_rounds={count}"
            )
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
                errors.append(
                    f"latest review round mismatch for {stage}: review_rounds={count} path={rel}"
                )
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

    for warning in warnings:
        print(f"WARNING {warning}")
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    if args.strict and warnings:
        return 1
    print(f"OK {task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
