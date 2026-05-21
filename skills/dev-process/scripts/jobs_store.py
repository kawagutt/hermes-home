"""v4 jobs.yaml load/save and job lifecycle helpers."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from handoff_validate import (
    HandoffValidationError,
    normalize_handoff_in,
    validate_handoff_markdown,
)
from job_roles import ROLES, profile_for_role, validate_session_id
from path_safety import (
    PathSafetyError,
    resolve_under_task,
    validate_artifact_out_path,
    validate_handoff_path,
)

JOBS_SCHEMA_VERSION = 4
JOB_ID_RE = re.compile(r"^job_(\d{4})$")

HANDOFF_IN_OPTIONAL_ROLES = frozenset({"spec"})
HANDOFF_OUT_OPTIONAL_ROLES = frozenset({"final_summary"})


class JobsStoreError(Exception):
    """jobs.yaml operation failure."""


def _require_yaml() -> None:
    if yaml is None:
        raise JobsStoreError("PyYAML is required (pip install pyyaml)")


def jobs_path(task_dir: Path) -> Path:
    return task_dir / "jobs.yaml"


def handoffs_dir(task_dir: Path) -> Path:
    return task_dir / "handoffs"


def load_jobs(task_dir: Path) -> dict[str, Any]:
    _require_yaml()
    path = jobs_path(task_dir)
    if not path.is_file():
        raise JobsStoreError(f"jobs.yaml not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise JobsStoreError("jobs.yaml root must be a mapping")
    if data.get("schema_version") != JOBS_SCHEMA_VERSION:
        raise JobsStoreError(
            f"unsupported jobs schema_version (expected {JOBS_SCHEMA_VERSION})"
        )
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise JobsStoreError("jobs must be a list")
    return data


def save_jobs(task_dir: Path, data: dict[str, Any]) -> None:
    _require_yaml()
    path = jobs_path(task_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def init_jobs(task_dir: Path, *, task_id: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": JOBS_SCHEMA_VERSION,
        "task_id": task_id,
        "jobs": [],
    }
    save_jobs(task_dir, data)
    handoffs_dir(task_dir).mkdir(parents=True, exist_ok=True)
    return data


def is_v4_task(task_dir: Path) -> bool:
    return jobs_path(task_dir).is_file()


def looks_like_pre_v4_task(task_dir: Path) -> bool:
    """True when state exists without jobs.yaml (historical pre-v4 task)."""
    if jobs_path(task_dir).is_file():
        return False
    state_path = task_dir / "state.yaml"
    if not state_path.is_file():
        return False
    try:
        with state_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f) if yaml else {}
    except OSError:
        return True
    if not isinstance(raw, dict):
        return False
    tid = str(raw.get("task_id") or "").strip()
    stage = str(raw.get("current_stage") or "").strip()
    return bool(tid or stage)


def next_job_id(data: dict[str, Any]) -> str:
    max_n = -1
    for job in data.get("jobs") or []:
        if not isinstance(job, dict):
            continue
        jid = str(job.get("id") or "")
        m = JOB_ID_RE.match(jid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"job_{max_n + 1:04d}"


def find_open_job(data: dict[str, Any]) -> dict[str, Any] | None:
    for job in reversed(data.get("jobs") or []):
        if isinstance(job, dict) and job.get("status") == "open":
            return job
    return None


def find_job(data: dict[str, Any], job_id: str) -> dict[str, Any] | None:
    for job in data.get("jobs") or []:
        if isinstance(job, dict) and job.get("id") == job_id:
            return job
    return None


def _next_handoff_basename(task_dir: Path) -> str:
    handoffs = handoffs_dir(task_dir)
    handoffs.mkdir(parents=True, exist_ok=True)
    max_n = -1
    for p in handoffs.glob("*.md"):
        m = re.match(r"^(\d{4})_", p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"{max_n + 1:04d}"


def allocate_handoff_out(task_dir: Path, role: str) -> str:
    n = _next_handoff_basename(task_dir)
    slug = role.replace("_", "-")
    rel = f"handoffs/{n}_{slug}.md"
    validate_handoff_path(task_dir, rel)
    return rel


def _normalize_handoff_in_list(task_dir: Path, paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        try:
            out.append(validate_handoff_path(task_dir, p))
        except PathSafetyError as exc:
            raise JobsStoreError(str(exc)) from exc
    return out


def _validate_handoff_in_content(task_dir: Path, paths: list[str]) -> None:
    for rel in paths:
        try:
            validate_handoff_markdown(task_dir / rel, label="handoff_in")
        except HandoffValidationError as exc:
            raise JobsStoreError(str(exc)) from exc


def _assert_session_unique(data: dict[str, Any], session_id: str) -> None:
    sid = session_id.strip()
    for job in data.get("jobs") or []:
        if not isinstance(job, dict) or job.get("status") != "closed":
            continue
        existing = str(job.get("session_id") or "").strip()
        if existing and existing == sid:
            raise JobsStoreError(
                f"J1: session_id {sid!r} already used by closed job {job.get('id')}"
            )


def _normalize_artifacts_out(
    task_dir: Path, artifacts_out: dict[str, str], *, require_exists: bool = True
) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, path in artifacts_out.items():
        k = key.strip()
        if not k:
            raise JobsStoreError("artifacts_out key must be non-empty")
        try:
            norm = validate_artifact_out_path(task_dir, path)
            resolved = resolve_under_task(task_dir, norm)
            if require_exists and not resolved.is_file():
                raise JobsStoreError(f"artifacts_out file missing: {norm}")
            out[k] = norm
        except PathSafetyError as exc:
            raise JobsStoreError(str(exc)) from exc
    return out


def _validate_review_round(review_round: int) -> None:
    if review_round < 1:
        raise JobsStoreError("review_round must be >= 1")


def open_job(
    task_dir: Path,
    *,
    role: str,
    handoff_in: list[str] | None = None,
    reviewer: str | None = None,
    review_target: str | None = None,
    review_round: int | None = None,
    stage_id: str | None = None,
) -> dict[str, Any]:
    if role not in ROLES:
        raise JobsStoreError(f"invalid role: {role!r}")

    data = load_jobs(task_dir)
    if find_open_job(data):
        raise JobsStoreError(
            "J6: an open job exists; run job close before starting the next job"
        )

    handoff_list = _normalize_handoff_in_list(task_dir, list(handoff_in or []))
    if role not in HANDOFF_IN_OPTIONAL_ROLES and not handoff_list:
        raise JobsStoreError(
            f"role {role!r} requires explicit --handoff-in (one or more paths); "
            "do not rely on previous job handoff_out"
        )
    if handoff_list:
        _validate_handoff_in_content(task_dir, handoff_list)

    job_id = next_job_id(data)
    profile = profile_for_role(role)
    handoff_out = allocate_handoff_out(task_dir, role)

    job: dict[str, Any] = {
        "id": job_id,
        "role": role,
        "session_id": None,
        "expected_profile": profile,
        "profile": profile,
        "observed_profile": "",
        "status": "open",
        "handoff_in": handoff_list,
        "handoff_out": handoff_out,
        "artifacts_out": {},
        "opened_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "closed_at": None,
    }
    if stage_id:
        job["stage_id"] = stage_id
    if role == "review_worker":
        if not reviewer or not review_target or review_round is None:
            raise JobsStoreError(
                "review_worker requires --reviewer, --review-target, --review-round"
            )
        _validate_review_round(int(review_round))
        job["reviewer"] = reviewer
        job["review_target"] = review_target
        job["review_round"] = int(review_round)
    if role == "review_synthesis":
        if not review_target or review_round is None:
            raise JobsStoreError(
                "review_synthesis requires --review-target and --review-round"
            )
        _validate_review_round(int(review_round))
        job["review_target"] = review_target
        job["review_round"] = int(review_round)

    data["jobs"].append(job)
    save_jobs(task_dir, data)
    return job


def close_job(
    task_dir: Path,
    *,
    job_id: str | None,
    session_id: str,
    model: str | None,
    artifacts_out: dict[str, str],
    usage: dict[str, Any] | None = None,
    observed_profile: str | None = None,
    skip_handoff_check: bool = False,
) -> dict[str, Any]:
    if not validate_session_id(session_id):
        raise JobsStoreError(f"invalid session_id: {session_id!r}")

    data = load_jobs(task_dir)
    open_j = find_open_job(data)
    if job_id:
        job = find_job(data, job_id)
        if not job:
            raise JobsStoreError(f"job not found: {job_id}")
        if job.get("status") != "open":
            raise JobsStoreError(f"job {job_id} is not open")
    elif open_j:
        job = open_j
    else:
        raise JobsStoreError("no open job to close")

    if job.get("session_id"):
        raise JobsStoreError(
            f"job {job.get('id')} already has session_id; cannot re-close"
        )

    sid = session_id.strip()
    _assert_session_unique(data, sid)

    role = str(job.get("role") or "")
    if not skip_handoff_check and role not in HANDOFF_OUT_OPTIONAL_ROLES:
        out_rel = job.get("handoff_out")
        if not isinstance(out_rel, str) or not out_rel.strip():
            raise JobsStoreError(f"job {job.get('id')}: missing handoff_out path")
        try:
            validate_handoff_markdown(task_dir / out_rel, label="handoff_out")
        except HandoffValidationError as exc:
            raise JobsStoreError(str(exc)) from exc

    norm_artifacts = _normalize_artifacts_out(task_dir, artifacts_out) if artifacts_out else {}

    expected = str(job.get("expected_profile") or job.get("profile") or "").strip()
    observed = (observed_profile or "").strip()
    job["observed_profile"] = observed
    if observed and expected and observed != expected:
        raise JobsStoreError(
            f"profile mismatch: expected {expected!r}, export shows {observed!r}"
        )

    job["session_id"] = sid
    job["status"] = "closed"
    job["closed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    if model:
        job["model"] = model
    if usage:
        job["usage"] = usage
    if norm_artifacts:
        existing = job.get("artifacts_out")
        if not isinstance(existing, dict):
            existing = {}
        existing.update(norm_artifacts)
        job["artifacts_out"] = existing

    save_jobs(task_dir, data)
    return job


def job_handoff_in_list(job: dict[str, Any]) -> list[str]:
    return normalize_handoff_in(job.get("handoff_in"))


def update_state_current_job(task_dir: Path, job_id: str | None) -> None:
    _require_yaml()
    state_path = task_dir / "state.yaml"
    if not state_path.is_file():
        return
    with state_path.open(encoding="utf-8") as f:
        state = yaml.safe_load(f) or {}
    if not isinstance(state, dict):
        return
    if job_id:
        state["current_job"] = job_id
    else:
        state.pop("current_job", None)
    with state_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, allow_unicode=True, sort_keys=False)
