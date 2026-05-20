#!/usr/bin/env python3
"""Shared primary-loop segment resolution from primary_segments.yaml + task state."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from model_resolve import ModelResolveError, get_review_depth_preset, load_yaml

PRIMARY_SEGMENTS_NAME = "primary_segments.yaml"
IMPLEMENTATION_PHASE_STAGE_RE = re.compile(r"^implementation_phase_(\d+)$")


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def default_primary_segments_path() -> Path:
    return _script_dir().parent / "config" / PRIMARY_SEGMENTS_NAME


def load_primary_segments(path: Path | None = None) -> dict[str, Any]:
    p = (path or default_primary_segments_path()).resolve()
    if not p.is_file():
        raise ModelResolveError(f"primary segments file not found: {p}")
    data = load_yaml(p)
    if not isinstance(data, dict) or "segments" not in data:
        raise ModelResolveError(f"{p}: root must contain segments")
    return data


def expand_implementation_phase_ids(
    state: dict[str, Any], task_dir: Path, pattern: str
) -> list[str]:
    ids: set[str] = set()
    rounds = state.get("review_rounds")
    if isinstance(rounds, dict):
        for key, raw in rounds.items():
            m = IMPLEMENTATION_PHASE_STAGE_RE.match(str(key))
            if not m:
                continue
            try:
                if int(raw) <= 0:
                    continue
            except (TypeError, ValueError):
                continue
            ids.add(pattern.format(phase=m.group(1)))

    phase = state.get("current_phase")
    if isinstance(phase, str) and phase.strip():
        p = phase.strip()
        if p.isdigit():
            ids.add(pattern.format(phase=p.zfill(2) if len(p) < 2 else p))

    artifacts = state.get("artifacts")
    if isinstance(artifacts, dict):
        pcl = artifacts.get("phase_checklists")
        if isinstance(pcl, str) and pcl.strip():
            path = task_dir / pcl.strip()
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r"implementation_phase_(\d+)", text):
                    ids.add(pattern.format(phase=m.group(1)))

    return sorted(ids)


def implementation_usage_stage_ids(
    state: dict[str, Any], task_dir: Path, pattern: str
) -> list[str]:
    """Per-phase ids when known; otherwise single implementation fallback row."""
    phase_ids = expand_implementation_phase_ids(state, task_dir, pattern)
    if phase_ids:
        return phase_ids
    return ["implementation"]


def resolve_required_usage_stage_ids(
    state: dict[str, Any], task_dir: Path, segments_cfg: dict[str, Any]
) -> list[str]:
    preset = get_review_depth_preset(state, task_dir)
    seg_root = segments_cfg.get("segments")
    if not isinstance(seg_root, dict):
        raise ModelResolveError("primary_segments.yaml: segments must be a mapping")
    preset_cfg = seg_root.get(preset)
    if not isinstance(preset_cfg, dict):
        raise ModelResolveError(
            f"primary_segments.yaml: no segment definition for preset {preset!r}"
        )

    required: list[str] = []
    static = preset_cfg.get("static")
    if isinstance(static, list):
        for entry in static:
            if isinstance(entry, dict):
                uid = entry.get("usage_stage_id")
                if isinstance(uid, str) and uid.strip():
                    required.append(uid.strip())

    dynamic = preset_cfg.get("dynamic")
    if isinstance(dynamic, dict):
        impl = dynamic.get("implementation_phases")
        if isinstance(impl, dict):
            pattern = str(
                impl.get("usage_stage_id_pattern") or "implementation_phase_{phase}"
            )
            if impl.get("required", True):
                required.extend(
                    implementation_usage_stage_ids(state, task_dir, pattern)
                )

    seen: set[str] = set()
    out: list[str] = []
    for uid in required:
        if uid not in seen:
            seen.add(uid)
            out.append(uid)
    return out


def is_required_primary_stage_id(
    preset: str,
    stage_id: str,
    state: dict[str, Any],
    task_dir: Path,
    segments_cfg: dict[str, Any] | None = None,
) -> bool:
    """True when stage_id is a required primary-loop usage stage for this preset."""
    if preset not in ("standard", "deep"):
        return False
    sid = stage_id.strip()
    if not sid:
        return False
    cfg = segments_cfg if segments_cfg is not None else load_primary_segments()
    required = resolve_required_usage_stage_ids(state, task_dir, cfg)
    return sid in required
