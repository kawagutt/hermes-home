#!/usr/bin/env python3
"""v4 Job Contract validator (jobs.yaml SOT). Pre-v4 tasks: not applicable."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from handoff_validate import validate_handoff_markdown
from job_roles import ROLES, ROLE_PROFILES, validate_session_id
from jobs_store import (
    HANDOFF_IN_OPTIONAL_ROLES,
    HANDOFF_OUT_OPTIONAL_ROLES,
    HandoffValidationError,
    find_open_job,
    is_v4_task,
    job_handoff_in_list,
    load_jobs,
)
PENDING_FINAL = "final_human_gate"
REVIEW_TARGETS_PATH = Path(__file__).resolve().parent.parent / "config" / "review_targets.yaml"


def _err(msg: str, errors: list[str]) -> None:
    errors.append(f"ERROR {msg}")


def _warn(msg: str, warnings: list[str]) -> None:
    warnings.append(f"WARNING {msg}")


def _str_field(state: dict, key: str) -> str:
    v = state.get(key)
    return v.strip() if isinstance(v, str) else ""


def _bool_field(mapping: dict, key: str) -> bool:
    return isinstance(mapping, dict) and mapping.get(key) is True


def _load_required_reviewers(preset: str) -> list[str]:
    if not REVIEW_TARGETS_PATH.is_file():
        return []
    with REVIEW_TARGETS_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    presets = data.get("presets") or {}
    block = presets.get(preset) or presets.get("standard") or {}
    reviewers = block.get("required_reviewers") or []
    if isinstance(reviewers, list):
        return [str(r).strip() for r in reviewers if str(r).strip()]
    return []


def _validate_handoff_path(task_dir: Path, rel: str, *, label: str, errors: list[str]) -> None:
    try:
        validate_handoff_markdown(task_dir / rel, label=label)
    except HandoffValidationError as exc:
        _err(str(exc), errors)


def _in_final_vicinity(state: dict) -> bool:
    if _str_field(state, "pending_human_gate") == PENDING_FINAL:
        return True
    if _str_field(state, "current_stage") in ("final", "final_human_gate"):
        return True
    if _bool_field(state.get("reviewed") or {}, "final"):
        return True
    if _bool_field(state.get("approved") or {}, "final_human_gate"):
        return True
    return False


def _closed_jobs_with_role(jobs_list: list[dict], role: str) -> list[dict]:
    return [
        j
        for j in jobs_list
        if j.get("role") == role and j.get("status") == "closed"
    ]


def _check_review_round_jobs(
    jobs_list: list[dict],
    *,
    target: str,
    round_num: int,
    preset: str,
    errors: list[str],
    label: str,
) -> None:
    workers = [
        j
        for j in jobs_list
        if j.get("role") == "review_worker"
        and j.get("status") == "closed"
        and j.get("review_target") == target
        and j.get("review_round") == round_num
    ]
    syntheses = [
        j
        for j in jobs_list
        if j.get("role") == "review_synthesis"
        and j.get("status") == "closed"
        and j.get("review_target") == target
        and j.get("review_round") == round_num
    ]
    if not workers:
        _err(f"{label}: no closed review_worker jobs for {target} round {round_num}", errors)
        return
    if not syntheses:
        _err(
            f"{label}: no closed review_synthesis job for {target} round {round_num}",
            errors,
        )
        return
    required = _load_required_reviewers(preset)
    found = {str(j.get("reviewer") or "") for j in workers}
    for reviewer in required:
        if reviewer not in found:
            _err(
                f"{label}: missing closed review_worker for reviewer {reviewer!r} "
                f"({target} round {round_num}, preset={preset})",
                errors,
            )
    worker_indices = [jobs_list.index(j) for j in workers]
    syn_indices = [jobs_list.index(j) for j in syntheses]
    if worker_indices and syn_indices:
        if min(syn_indices) <= max(worker_indices):
            _err(
                f"{label}: review_synthesis must be closed after all review_workers "
                f"for {target} round {round_num}",
                errors,
            )


def _review_targets_from_state(state: dict) -> list[tuple[str, int]]:
    """Review targets that state marks as reviewed with a completed round."""
    reviewed = state.get("reviewed")
    rounds = state.get("review_rounds")
    if not isinstance(reviewed, dict):
        return []
    if not isinstance(rounds, dict):
        rounds = {}
    out: list[tuple[str, int]] = []
    for key in ("spec", "plan", "test", "final"):
        if reviewed.get(key) is True:
            try:
                rnd = int(rounds.get(key) or 0)
            except (TypeError, ValueError):
                rnd = 0
            if rnd >= 1:
                out.append((key, rnd))
    for key, val in rounds.items():
        if not isinstance(key, str) or not key.startswith("implementation_phase_"):
            continue
        try:
            rnd = int(val or 0)
        except (TypeError, ValueError):
            continue
        if rnd >= 1 and reviewed.get(key) is True:
            out.append((key, rnd))
    return out


def _check_all_reviewed_rounds(
    state: dict, jobs_list: list[dict], errors: list[str], *, strict: bool
) -> None:
    if not strict:
        return
    preset = _str_field(state, "review_depth_preset").lower() or "standard"
    for target, rnd in _review_targets_from_state(state):
        _check_review_round_jobs(
            jobs_list,
            target=target,
            round_num=rnd,
            preset=preset,
            errors=errors,
            label=f"strict reviewed.{target}",
        )


def _check_final_strict(state: dict, jobs_list: list[dict], errors: list[str]) -> None:
    preset = _str_field(state, "review_depth_preset").lower() or "standard"
    for role in ("final_review", "final_summary"):
        if not _closed_jobs_with_role(jobs_list, role):
            _err(f"strict final: missing closed {role} job", errors)

    rounds = state.get("review_rounds")
    final_round = 1
    if isinstance(rounds, dict):
        try:
            final_round = max(1, int(rounds.get("final") or 0))
        except (TypeError, ValueError):
            final_round = 1
    if _bool_field(state.get("reviewed") or {}, "final") or _in_final_vicinity(state):
        _check_review_round_jobs(
            jobs_list,
            target="final",
            round_num=final_round,
            preset=preset,
            errors=errors,
            label="strict final",
        )


def _check_current_job(state: dict, open_j: dict[str, Any] | None, errors: list[str]) -> None:
    current = _str_field(state, "current_job")
    if open_j:
        oid = str(open_j.get("id") or "")
        if current != oid:
            _err(
                f"state.current_job={current!r} but open job is {oid!r}",
                errors,
            )
    elif current:
        _err(f"state.current_job={current!r} but no open job in jobs.yaml", errors)


def validate_v4(task_dir: Path, *, strict: bool) -> tuple[int, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not is_v4_task(task_dir):
        msg = (
            "This task has no jobs.yaml and appears to be pre-v4. "
            "v4 validation is not applicable — use validate_model_governance.py --strict "
            "for legacy tasks."
        )
        print(msg, file=sys.stderr)
        return 0, errors, warnings

    try:
        data = load_jobs(task_dir)
    except Exception as exc:
        _err(str(exc), errors)
        return 1, errors, warnings

    state: dict[str, Any] = {}
    state_path = task_dir / "state.yaml"
    if state_path.is_file():
        with state_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if isinstance(raw, dict):
            state = raw

    open_j = find_open_job(data)
    _check_current_job(state, open_j, errors)

    if open_j and strict:
        _err(f"J6: open job {open_j.get('id')} must be closed before strict validation", errors)

    session_to_job: dict[str, str] = {}
    jobs_list = [j for j in data.get("jobs") or [] if isinstance(j, dict)]

    for job in jobs_list:
        jid = str(job.get("id") or "?")
        role = str(job.get("role") or "")
        status = str(job.get("status") or "")
        sid_raw = job.get("session_id")
        sid = str(sid_raw).strip() if sid_raw else ""

        if role not in ROLES:
            _err(f"job {jid}: invalid role {role!r}", errors)

        expected_profile = ROLE_PROFILES.get(role, "")
        actual = str(job.get("profile") or "")
        if expected_profile and actual != expected_profile:
            _err(
                f"job {jid}: profile {actual!r} != role mapping {expected_profile!r}",
                errors,
            )

        if role == "review_worker":
            for field in ("reviewer", "review_target", "review_round"):
                if job.get(field) in (None, ""):
                    _err(f"job {jid}: review_worker missing {field}", errors)
        if role == "review_synthesis":
            for field in ("review_target", "review_round"):
                if job.get(field) in (None, ""):
                    _err(f"job {jid}: review_synthesis missing {field}", errors)

        handoff_in = job_handoff_in_list(job)
        if role not in HANDOFF_IN_OPTIONAL_ROLES and not handoff_in:
            _err(f"job {jid}: handoff_in required for role {role!r}", errors)
        for rel in handoff_in:
            if not (task_dir / rel).is_file():
                _err(f"job {jid}: handoff_in file missing: {rel}", errors)
            elif strict:
                _validate_handoff_path(task_dir, rel, label="handoff_in", errors=errors)

        if status == "open":
            if sid:
                _err(f"job {jid}: open job must not have session_id yet", errors)
            continue

        if status != "closed":
            _err(f"job {jid}: status must be open or closed, got {status!r}", errors)
            continue

        if not sid or not validate_session_id(sid):
            _err(f"job {jid}: closed job missing valid session_id", errors)

        if sid:
            if sid in session_to_job:
                _err(
                    f"J1: duplicate session_id {sid!r} in jobs "
                    f"{session_to_job[sid]} and {jid}",
                    errors,
                )
            else:
                session_to_job[sid] = jid

        if not job.get("closed_at"):
            _warn(f"job {jid}: closed without closed_at", warnings)

        if status == "closed":
            exp_prof = str(
                job.get("expected_profile") or job.get("profile") or expected_profile
            ).strip()
            obs_prof = str(job.get("observed_profile") or "").strip()
            if obs_prof and exp_prof and obs_prof != exp_prof:
                _err(
                    f"job {jid}: observed_profile {obs_prof!r} != expected {exp_prof!r}",
                    errors,
                )
            elif strict and exp_prof and not obs_prof:
                _warn(
                    f"job {jid}: observed_profile missing in export "
                    f"(cannot verify Hermes profile {exp_prof!r})",
                    warnings,
                )

        if role not in HANDOFF_OUT_OPTIONAL_ROLES:
            out_rel = job.get("handoff_out")
            if not isinstance(out_rel, str) or not out_rel.strip():
                _err(f"job {jid}: missing handoff_out path", errors)
            elif strict:
                _validate_handoff_path(
                    task_dir, str(out_rel), label="handoff_out", errors=errors
                )

    for idx, job in enumerate(jobs_list):
        if job.get("role") != "review_synthesis" or job.get("status") != "closed":
            continue
        jid = job.get("id")
        target = job.get("review_target")
        rnd = job.get("review_round")
        workers = [
            j
            for j in jobs_list[:idx]
            if j.get("role") == "review_worker"
            and j.get("status") == "closed"
            and j.get("review_target") == target
            and j.get("review_round") == rnd
        ]
        if not workers:
            _err(
                f"job {jid}: review_synthesis requires prior closed review_worker "
                f"for {target} round {rnd}",
                errors,
            )

    for legacy in (
        "last_hermes_profile",
        "last_dev_process_action",
        "last_resolution_source",
        "last_model_stage_id",
    ):
        if state.get(legacy):
            _warn(
                f"v4 task should not set state.{legacy} (use jobs.yaml instead)",
                warnings,
            )

    if strict:
        _check_all_reviewed_rounds(state, jobs_list, errors, strict=True)
        if _in_final_vicinity(state):
            _check_final_strict(state, jobs_list, errors)
        approved = state.get("approved") or {}
        if isinstance(approved, dict) and approved.get("final_human_gate") is True and errors:
            _err("J7: final_human_gate approved but strict validation has errors", errors)

    code = 1 if errors else 0
    return code, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", nargs="?", default=None)
    parser.add_argument("--task-dir", dest="task_dir_flag", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    raw = args.task_dir_flag or args.task_dir
    if not raw:
        print("validate_jobs_v4.py: task-dir required", file=sys.stderr)
        return 2

    task_dir = Path(raw).resolve()
    code, errors, warnings = validate_v4(task_dir, strict=args.strict)

    for w in warnings:
        print(w, file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)

    if code == 0 and not errors:
        print("OK v4 job contract validation")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
