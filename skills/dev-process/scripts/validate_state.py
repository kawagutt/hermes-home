#!/usr/bin/env python3
"""Validate a dev-process task state.yaml with deterministic local checks."""

from __future__ import annotations

import argparse
import functools
import re
from pathlib import Path
from typing import Any

import yaml

POLICY_PATH = Path(__file__).resolve().parent.parent / "config" / "model_policy.yaml"
STAGE_IDS_PATH = Path(__file__).resolve().parent.parent / "config" / "stage_ids.yaml"

LATEST_RE = re.compile(
    r"^reviews/(?P<stage>[^/]+)/round_(?P<num>\d{2,})/synthesis\.md$"
)
NUMBERED_TASK_ROOT_MD_RE = re.compile(r"^\d{4}_[^/]+\.md$")

PENDING_SPEC = "human_spec_gate"
PENDING_FINAL = "final_human_gate"
VALID_PENDING = frozenset({"", PENDING_SPEC, PENDING_FINAL})

# Normal current_stage while waiting at each gate (Task 1: pending is authoritative).
SPEC_PENDING_OK_STAGES = frozenset({"spec", "human_spec_gate"})
FINAL_PENDING_OK_STAGES = frozenset({"final", "final_human_gate"})


@functools.lru_cache(maxsize=1)
def load_state_stage_ids() -> frozenset[str]:
    if not STAGE_IDS_PATH.is_file():
        raise SystemExit(f"ERROR stage ids file not found: {STAGE_IDS_PATH}")
    with STAGE_IDS_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    stages = data.get("state_stages") or []
    if not isinstance(stages, list):
        raise SystemExit(f"ERROR state_stages must be a list: {STAGE_IDS_PATH}")
    return frozenset(str(s).strip() for s in stages if str(s).strip())


def gate_pending_advanced_stages() -> tuple[frozenset[str], frozenset[str]]:
    """Stages in stage_ids.yaml that warrant a WARNING while at each human gate wait."""
    all_stages = load_state_stage_ids()
    return (
        all_stages - SPEC_PENDING_OK_STAGES,
        all_stages - FINAL_PENDING_OK_STAGES,
    )


def _str_field(state: dict, key: str) -> str:
    value = state.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value).strip()
    return value.strip()


def _bool_field(mapping: dict, key: str) -> bool:
    return mapping.get(key) is True


def _current_stage_past_gate_wait(
    current_stage: str,
    ok_stages: frozenset[str],
    advanced_stages: frozenset[str],
) -> bool:
    if not current_stage:
        return False
    if current_stage in ok_stages:
        return False
    if current_stage in advanced_stages:
        return True
    # Legacy or future stage ids not yet listed in stage_ids.yaml.
    return True


def check_gate_consistency(state: dict, errors: list[str], warnings: list[str]) -> None:
    """Human gate state invariants (pending_human_gate is authoritative)."""
    pending = _str_field(state, "pending_human_gate")
    if pending not in VALID_PENDING:
        errors.append(
            f"pending_human_gate {pending!r} is invalid "
            f"(expected '', {PENDING_SPEC!r}, or {PENDING_FINAL!r})"
        )

    approved = state.get("approved") or {}
    reviewed = state.get("reviewed") or {}
    if not isinstance(approved, dict):
        approved = {}
    if not isinstance(reviewed, dict):
        reviewed = {}

    final_reviewed = _bool_field(reviewed, "final")
    spec_reviewed = _bool_field(reviewed, "spec")
    final_approved = _bool_field(approved, "final_human_gate")
    spec_approved = _bool_field(approved, "human_spec_gate")

    if final_reviewed and not final_approved and pending != PENDING_FINAL:
        errors.append(
            "reviewed.final is true but pending_human_gate is not "
            f"{PENDING_FINAL!r} (got {pending!r})"
        )
    if spec_reviewed and not spec_approved and pending != PENDING_SPEC:
        errors.append(
            "reviewed.spec is true but pending_human_gate is not "
            f"{PENDING_SPEC!r} (got {pending!r})"
        )
    if pending == PENDING_FINAL and final_approved:
        errors.append(
            f"pending_human_gate is {PENDING_FINAL!r} but "
            "approved.final_human_gate is already true"
        )
    if pending == PENDING_SPEC and spec_approved:
        errors.append(
            f"pending_human_gate is {PENDING_SPEC!r} but "
            "approved.human_spec_gate is already true"
        )

    if pending and not _str_field(state, "gate_prompted_at"):
        warnings.append(
            "pending_human_gate is set but gate_prompted_at is empty "
            "(gate presenter should set both before chat STOP)"
        )

    spec_advanced, final_advanced = gate_pending_advanced_stages()
    current_stage = _str_field(state, "current_stage")
    if pending == PENDING_SPEC and _current_stage_past_gate_wait(
        current_stage, SPEC_PENDING_OK_STAGES, spec_advanced
    ):
        warnings.append(
            f"pending_human_gate is {PENDING_SPEC!r} but current_stage is "
            f"{current_stage!r} (orchestrator may have advanced past spec gate wait)"
        )
    if pending == PENDING_FINAL and _current_stage_past_gate_wait(
        current_stage, FINAL_PENDING_OK_STAGES, final_advanced
    ):
        warnings.append(
            f"pending_human_gate is {PENDING_FINAL!r} but current_stage is "
            f"{current_stage!r} (orchestrator may have advanced past final gate wait)"
        )


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

    check_gate_consistency(state, errors, warnings)

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
