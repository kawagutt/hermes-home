#!/usr/bin/env python3
"""Validate primary model governance and review manifest session evidence."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

try:
    import yaml
except ImportError:
    print(
        "validate_model_governance.py: PyYAML is required (pip install pyyaml)",
        file=sys.stderr,
    )
    raise SystemExit(2) from None

from model_resolve import (
    ModelResolveError,
    default_policy_path,
    get_review_depth_preset,
    load_task_state,
    load_yaml,
    validate_policy,
)

PRIMARY_SEGMENTS_NAME = "primary_segments.yaml"
SESSION_ID_RE = re.compile(r"^\d{8}_\d{6}_[0-9a-f]{6}$", re.IGNORECASE)
INVALID_SESSION = frozenset(
    {"", "unknown", "[session]", "<session-id>", "<id>", "n/a", "na"}
)
GOVERNANCE_WAIVER_MARKERS = (
    "unknown waiver",
    "model usage waiver",
    "pyyaml",
    "helper env",
    "cannot observe",
    "session lost",
    "session reuse waiver",
    "duplicate session waiver",
    "primary session reuse",
)


@dataclass
class Issue:
    level: Literal["error", "warning"]
    message: str


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def default_primary_segments_path() -> Path:
    return _script_dir().parent / "config" / PRIMARY_SEGMENTS_NAME


def default_review_targets_path() -> Path:
    return _script_dir().parent / "config" / "review_targets.yaml"


def load_primary_segments(path: Path | None = None) -> dict[str, Any]:
    p = (path or default_primary_segments_path()).resolve()
    if not p.is_file():
        raise ModelResolveError(f"primary segments file not found: {p}")
    data = load_yaml(p)
    if not isinstance(data, dict) or "segments" not in data:
        raise ModelResolveError(f"{p}: root must contain segments")
    return data


def load_review_targets(path: Path | None = None) -> dict[str, Any]:
    p = (path or default_review_targets_path()).resolve()
    if not p.is_file():
        raise ModelResolveError(f"review targets file not found: {p}")
    data = load_yaml(p)
    if not isinstance(data, dict):
        raise ModelResolveError(f"{p}: root must be a mapping")
    return data


def infer_model_usage_required(state: dict[str, Any], task_dir: Path) -> bool:
    raw = state.get("model_usage_required")
    if raw is True:
        return True
    if raw is False:
        return False

    plan_path = _plan_path(state, task_dir)
    if plan_path is not None:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
        m = re.search(
            r"\*\*Model usage record required\?\*\s*\|\s*\*?\*?\s*(yes|no)\b",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).lower() == "yes"

    preset = get_review_depth_preset(state, task_dir)
    return preset in ("standard", "deep")


def _plan_path(state: dict[str, Any], task_dir: Path) -> Path | None:
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    plan_name = artifacts.get("plan")
    if not isinstance(plan_name, str) or not plan_name.strip():
        return None
    path = task_dir / plan_name.strip()
    return path if path.is_file() else None


def parse_session_id(cell: str) -> str | None:
    if not isinstance(cell, str):
        return None
    raw = cell.strip()
    if not raw:
        return None
    if raw.startswith("`") and raw.endswith("`"):
        raw = raw[1:-1].strip()
    low = raw.lower()
    if low in INVALID_SESSION:
        return None
    if SESSION_ID_RE.match(raw):
        return raw
    return None


def parse_model_usage_table(text: str) -> tuple[dict[str, str], list[str]]:
    """Return stage_id -> session_id (last row wins) and parse errors."""
    rows: dict[str, str] = {}
    errors: list[str] = []
    header_idx: int | None = None
    col_stage: int | None = None
    col_session: int | None = None

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        lowered = [c.lower() for c in cells]
        if header_idx is None and "stage id" in lowered and "session" in lowered:
            header_idx = i
            try:
                col_stage = lowered.index("stage id")
            except ValueError:
                errors.append("model_usage table missing Stage id column")
                return rows, errors
            try:
                col_session = lowered.index("session")
            except ValueError:
                errors.append("model_usage table missing Session column")
                return rows, errors
            continue
        if header_idx is None or col_stage is None or col_session is None:
            continue
        if all(not c or set(c) <= {"-", ":"} for c in cells):
            continue
        if len(cells) <= max(col_stage, col_session):
            continue
        stage_raw = cells[col_stage].strip().strip("`")
        if not stage_raw or stage_raw.lower() == "stage id":
            continue
        session_cell = cells[col_session]
        session_raw = session_cell.strip().strip("`").strip()
        sid = parse_session_id(session_cell)
        if sid:
            rows[stage_raw] = sid
        elif session_raw.lower() == "unknown":
            rows[stage_raw] = "unknown"
    return rows, errors


def expand_implementation_phase_ids(
    state: dict[str, Any], task_dir: Path, pattern: str
) -> list[str]:
    ids: set[str] = set()
    rounds = state.get("review_rounds")
    if isinstance(rounds, dict):
        for key, raw in rounds.items():
            m = re.match(r"implementation_phase_(\d+)$", str(key))
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


def _governance_waiver_text(task_dir: Path, state: dict[str, Any]) -> str:
    blobs: list[str] = []
    artifacts = state.get("artifacts")
    if isinstance(artifacts, dict):
        for key in ("timeline", "plan"):
            name = artifacts.get(key)
            if isinstance(name, str) and name.strip():
                path = task_dir / name.strip()
                if path.is_file():
                    blobs.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(blobs).lower()


def _has_model_governance_waiver(
    task_dir: Path, state: dict[str, Any], stage_id: str
) -> bool:
    combined = _governance_waiver_text(task_dir, state)
    if stage_id.lower() not in combined:
        return False
    return any(m in combined for m in GOVERNANCE_WAIVER_MARKERS)


def _has_duplicate_session_waiver(
    task_dir: Path, state: dict[str, Any], stages: list[str]
) -> bool:
    combined = _governance_waiver_text(task_dir, state)
    reuse_markers = (
        "session reuse waiver",
        "duplicate session waiver",
        "primary session reuse",
    )
    if any(m in combined for m in reuse_markers):
        return True
    return any(_has_model_governance_waiver(task_dir, state, st) for st in stages)


def _latest_review_rounds(state: dict[str, Any]) -> dict[str, int]:
    rounds = state.get("review_rounds")
    if not isinstance(rounds, dict):
        return {}
    out: dict[str, int] = {}
    for stage, raw in rounds.items():
        if not isinstance(stage, str) or not stage.strip():
            continue
        stage_norm = stage.strip()
        if stage_norm.startswith("implementation_phase_"):
            continue
        try:
            n = int(raw)
        except (TypeError, ValueError):
            continue
        if n > 0:
            out[stage_norm] = n
    return out


def _manifest_path(task_dir: Path, stage: str, round_num: int) -> Path:
    return task_dir / "reviews" / stage / f"round_{round_num:02d}" / "review_manifest.yaml"


def validate_manifest(
    manifest_path: Path,
    *,
    preset: str,
    targets: dict[str, Any],
    strict: bool,
) -> list[Issue]:
    issues: list[Issue] = []
    if not manifest_path.is_file():
        issues.append(
            Issue("error" if strict else "warning", f"missing {manifest_path}")
        )
        return issues
    try:
        data = load_yaml(manifest_path)
    except Exception as exc:
        issues.append(Issue("error", f"malformed {manifest_path}: {exc}"))
        return issues
    if not isinstance(data, dict):
        issues.append(Issue("error", f"malformed {manifest_path}: root not a mapping"))
        return issues

    presets = targets.get("presets")
    if not isinstance(presets, dict):
        issues.append(Issue("error", "review_targets.yaml: presets missing"))
        return issues
    preset_cfg = presets.get(preset)
    if not isinstance(preset_cfg, dict):
        issues.append(Issue("error", f"unknown preset in manifest check: {preset!r}"))
        return issues
    required = preset_cfg.get("required_reviewers")
    if not isinstance(required, list):
        issues.append(Issue("error", f"preset {preset!r} missing required_reviewers"))
        return issues

    reviewers = data.get("reviewers")
    if not isinstance(reviewers, dict):
        issues.append(Issue("error", f"{manifest_path}: reviewers block missing"))
        return issues

    reviewer_sessions: list[str] = []
    for agent in required:
        name = str(agent).strip()
        block = reviewers.get(name)
        if not isinstance(block, dict):
            issues.append(
                Issue("error", f"{manifest_path}: missing reviewer entry {name!r}")
            )
            continue
        sid = block.get("session_id")
        if not isinstance(sid, str) or not parse_session_id(sid):
            issues.append(
                Issue(
                    "error" if strict else "warning",
                    f"{manifest_path}: reviewer {name!r} missing session_id",
                )
            )
        else:
            reviewer_sessions.append(sid.strip())

    synthesis = data.get("synthesis")
    if not isinstance(synthesis, dict):
        issues.append(Issue("error", f"{manifest_path}: synthesis block missing"))
        return issues
    syn_sid_raw = synthesis.get("session_id")
    syn_sid = (
        parse_session_id(syn_sid_raw)
        if isinstance(syn_sid_raw, str)
        else None
    )
    if not syn_sid:
        issues.append(
            Issue(
                "error" if strict else "warning",
                f"{manifest_path}: synthesis missing session_id",
            )
        )
    elif syn_sid in reviewer_sessions:
        issues.append(
            Issue(
                "error",
                f"{manifest_path}: synthesis session_id must differ from reviewers",
            )
        )
    return issues


def validate_task(
    task_dir: Path,
    *,
    strict: bool = False,
    segments_path: Path | None = None,
    policy_path: Path | None = None,
    targets_path: Path | None = None,
) -> list[Issue]:
    task_dir = task_dir.resolve()
    state_path = task_dir / "state.yaml"
    if not state_path.is_file():
        return [Issue("error", f"missing {state_path}")]

    state = load_task_state(task_dir)
    issues: list[Issue] = []
    usage_required = infer_model_usage_required(state, task_dir)

    artifacts = state.get("artifacts")
    model_usage_name: str | None = None
    if isinstance(artifacts, dict):
        raw = artifacts.get("model_usage")
        if isinstance(raw, str) and raw.strip():
            model_usage_name = raw.strip()

    if usage_required and not model_usage_name:
        issues.append(
            Issue(
                "error" if strict else "warning",
                "model_usage_required but artifacts.model_usage unset",
            )
        )

    usage_rows: dict[str, str] = {}
    if model_usage_name:
        mu_path = task_dir / model_usage_name
        if not mu_path.is_file():
            issues.append(Issue("error", f"missing model_usage artifact: {mu_path}"))
        else:
            usage_rows, parse_errors = parse_model_usage_table(
                mu_path.read_text(encoding="utf-8", errors="replace")
            )
            for err in parse_errors:
                issues.append(Issue("error", err))

    if usage_required:
        try:
            segments_cfg = load_primary_segments(segments_path)
            required_ids = resolve_required_usage_stage_ids(
                state, task_dir, segments_cfg
            )
        except ModelResolveError as exc:
            issues.append(Issue("error", str(exc)))
            required_ids = []
        except Exception as exc:
            issues.append(Issue("error", f"primary segments: {exc}"))
            required_ids = []

        session_by_stage: dict[str, str | None] = {}
        for uid in required_ids:
            cell = usage_rows.get(uid, "")
            cell_stripped = cell.strip().strip("`").strip() if cell else ""
            sid = parse_session_id(cell) if cell else None
            is_unknown = cell_stripped.lower() == "unknown"
            session_by_stage[uid] = sid

            if strict:
                if sid:
                    pass
                elif is_unknown:
                    if not _has_model_governance_waiver(task_dir, state, uid):
                        issues.append(
                            Issue(
                                "error",
                                f"unresolved unknown Session for stage {uid}",
                            )
                        )
                else:
                    issues.append(
                        Issue(
                            "error",
                            f"required primary usage row missing/invalid: {uid}",
                        )
                    )
            elif is_unknown and not _has_model_governance_waiver(
                task_dir, state, uid
            ):
                issues.append(
                    Issue("warning", f"unresolved unknown Session for stage {uid}")
                )

        dupes: dict[str, list[str]] = {}
        for uid, sid in session_by_stage.items():
            if sid:
                dupes.setdefault(sid, []).append(uid)
        for sid, stages in dupes.items():
            if len(stages) < 2:
                continue
            msg = (
                f"duplicate primary session_id {sid} on stages: "
                + ", ".join(stages)
            )
            waiver = _has_duplicate_session_waiver(task_dir, state, stages)
            if strict and not waiver:
                issues.append(Issue("error", msg))
            elif not strict:
                issues.append(Issue("warning", msg))

    if strict and not state.get("last_hermes_profile"):
        issues.append(
            Issue(
                "warning",
                "last_hermes_profile unset (supplemental; session rows are primary evidence)",
            )
        )

    preset = get_review_depth_preset(state, task_dir)
    targets = load_review_targets(targets_path)
    latest = _latest_review_rounds(state)
    for stage, rnd in latest.items():
        mpath = _manifest_path(task_dir, stage, rnd)
        round_issues = validate_manifest(
            mpath, preset=preset, targets=targets, strict=strict
        )
        issues.extend(round_issues)

        if rnd > 1 and not strict:
            older = _manifest_path(task_dir, stage, rnd - 1)
            if not older.is_file():
                issues.append(
                    Issue("warning", f"older review round missing manifest: {older}")
                )

    if policy_path:
        try:
            validate_policy(load_yaml(policy_path))
        except Exception as exc:
            issues.append(Issue("warning", f"policy validation: {exc}"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", help="Path to .hermes/tasks/<task-id>")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on duplicate sessions, missing primary rows, unresolved unknown",
    )
    parser.add_argument("--segments", default=None, help="primary_segments.yaml path")
    parser.add_argument("--policy", default=None, help="model_policy.yaml path")
    parser.add_argument("--targets", default=None, help="review_targets.yaml path")
    args = parser.parse_args()

    task_dir = Path(args.task_dir)
    policy = Path(args.policy).resolve() if args.policy else default_policy_path()
    segments = Path(args.segments).resolve() if args.segments else None
    targets = Path(args.targets).resolve() if args.targets else None

    try:
        issues = validate_task(
            task_dir,
            strict=args.strict,
            segments_path=segments,
            policy_path=policy,
            targets_path=targets,
        )
    except ModelResolveError as exc:
        print(f"validate_model_governance.py: {exc}", file=sys.stderr)
        return 2

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    for i in issues:
        prefix = "ERROR" if i.level == "error" else "WARNING"
        print(f"{prefix}: {i.message}")

    if errors:
        return 1
    if warnings:
        print(f"OK with {len(warnings)} warning(s)")
        return 0
    print("OK model governance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
