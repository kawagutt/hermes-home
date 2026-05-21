"""Safe relative paths under a task directory (v4 helpers)."""

from __future__ import annotations

from pathlib import Path


class PathSafetyError(Exception):
    """Invalid or unsafe task-relative path."""


def _normalize_rel(rel: str) -> str:
    raw = rel.strip().replace("\\", "/")
    if not raw:
        raise PathSafetyError("empty path")
    if raw.startswith("/"):
        raise PathSafetyError(f"absolute path not allowed: {rel!r}")
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if ".." in parts:
        raise PathSafetyError(f"path must not contain '..': {rel!r}")
    return "/".join(parts)


def resolve_under_task(task_dir: Path, rel: str) -> Path:
    """Resolve rel under task_dir; reject escape via '..'."""
    norm = _normalize_rel(rel)
    base = task_dir.resolve()
    path = (base / norm).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise PathSafetyError(f"path escapes task dir: {rel!r}") from exc
    return path


def validate_handoff_path(task_dir: Path, rel: str) -> str:
    norm = _normalize_rel(rel)
    if not norm.startswith("handoffs/"):
        raise PathSafetyError(f"handoff path must be under handoffs/: {rel!r}")
    resolve_under_task(task_dir, norm)
    return norm


def validate_artifact_out_path(task_dir: Path, rel: str) -> str:
    norm = _normalize_rel(rel)
    if norm.startswith("handoffs/"):
        raise PathSafetyError(f"artifacts_out must not use handoffs/: {rel!r}")
    resolve_under_task(task_dir, norm)
    return norm


def validate_generated_out_path(task_dir: Path, rel: str) -> str:
    """Allow only generated/* under task dir."""
    norm = _normalize_rel(rel)
    if not norm.startswith("generated/"):
        raise PathSafetyError(f"render output must be under generated/: {rel!r}")
    resolve_under_task(task_dir, norm)
    return norm
