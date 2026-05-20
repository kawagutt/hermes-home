#!/usr/bin/env python3
"""Resolve review worker jobs and maintain review_manifest.yaml per review round.

Does not launch Hermes and does not update state.yaml last_* fields (primary loop only).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:  # pragma: no cover
    print("dp_review_job.py: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2) from e

from model_resolve import (
    ModelResolveError,
    get_review_depth_preset,
    load_task_state,
    load_yaml,
    resolve_for_task,
    validate_policy,
)
from session_usage import build_summary, format_usage_cost, load_session_export

REVIEW_TARGETS_NAME = "review_targets.yaml"
MANIFEST_NAME = "review_manifest.yaml"


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def default_review_targets_path() -> Path:
    return _script_dir().parent / "config" / REVIEW_TARGETS_NAME


def default_policy_path() -> Path:
    return _script_dir().parent / "config" / "model_policy.yaml"


def load_review_targets(path: Path | None = None) -> dict[str, Any]:
    p = (path or default_review_targets_path()).resolve()
    if not p.is_file():
        raise ModelResolveError(f"review targets file not found: {p}")
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ModelResolveError(f"{p}: root must be a mapping")
    agents = data.get("agents")
    presets = data.get("presets")
    if not isinstance(agents, list) or not agents:
        raise ModelResolveError(f"{p}: agents must be a non-empty list")
    if not isinstance(presets, dict) or not presets:
        raise ModelResolveError(f"{p}: presets must be a non-empty mapping")
    return data


def canonical_agents(targets: dict[str, Any]) -> set[str]:
    return {str(a).strip() for a in targets["agents"] if str(a).strip()}


def validate_reviewer_agent(agent: str, targets: dict[str, Any]) -> str:
    name = agent.strip()
    allowed = canonical_agents(targets)
    if name not in allowed:
        listed = ", ".join(sorted(allowed))
        raise ModelResolveError(
            f"unknown review agent {name!r} (expected one of: {listed})"
        )
    return name


def reviewer_action(agent: str) -> str:
    agent = agent.strip()
    if not agent or agent == "synthesis":
        raise ModelResolveError(f"invalid review agent: {agent!r}")
    return f"review_{agent}"


def resolve_synthesis_action(*, review_stage: str, preset_cfg: dict[str, Any]) -> str:
    stage = review_stage.strip().lower()
    if stage == "final" or stage.startswith("final_"):
        return "review_synthesis_final"
    action = preset_cfg.get("synthesis_action")
    if not isinstance(action, str) or not action.strip():
        raise ModelResolveError(
            "preset missing synthesis_action in review_targets.yaml"
        )
    return action.strip()


def round_dir(task_dir: Path, review_stage: str, round_num: int) -> Path:
    return task_dir / "reviews" / review_stage / f"round_{round_num:02d}"


def manifest_path(task_dir: Path, review_stage: str, round_num: int) -> Path:
    return round_dir(task_dir, review_stage, round_num) / MANIFEST_NAME


def reviewer_output_filename(agent: str) -> str:
    return f"{agent.strip()}.md"


def _empty_worker_entry(
    *,
    action: str,
    role: str,
    hermes_profile: str,
    output: str,
) -> dict[str, str]:
    return {
        "action": action,
        "role": role,
        "hermes_profile": hermes_profile,
        "output": output,
        "session_id": "",
        "usage_evidence": "",
    }


def build_manifest_skeleton(
    *,
    review_stage: str,
    round_num: int,
    preset: str,
    required_reviewers: list[str],
    synthesis_action: str,
    policy_path: Path,
    task_dir: Path,
    targets: dict[str, Any],
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "review_stage": review_stage,
        "round": round_num,
        "preset": preset,
        "reviewers": {},
        "synthesis": {},
    }
    allowed = canonical_agents(targets)
    for agent in required_reviewers:
        name = str(agent).strip()
        if name not in allowed:
            raise ModelResolveError(
                f"required_reviewer {name!r} not in review_targets agents"
            )
        action = reviewer_action(name)
        resolved = resolve_for_task(
            task_dir,
            policy_path=policy_path,
            action=action,
        )
        manifest["reviewers"][name] = _empty_worker_entry(
            action=action,
            role=resolved["role"],
            hermes_profile=resolved["hermes_profile"],
            output=reviewer_output_filename(name),
        )
    syn_resolved = resolve_for_task(
        task_dir,
        policy_path=policy_path,
        action=synthesis_action,
    )
    manifest["synthesis"] = _empty_worker_entry(
        action=synthesis_action,
        role=syn_resolved["role"],
        hermes_profile=syn_resolved["hermes_profile"],
        output="synthesis.md",
    )
    return manifest


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            manifest, f, sort_keys=False, allow_unicode=True, default_flow_style=False
        )


def init_manifest_file(
    *,
    mpath: Path,
    force: bool,
    manifest: dict[str, Any],
) -> None:
    rdir = mpath.parent
    if not rdir.is_dir():
        raise ModelResolveError(
            f"review round directory not found: {rdir} (run review_round.py --create first)"
        )
    if mpath.is_file() and not force:
        raise ModelResolveError(
            f"review manifest already exists: {mpath} (use --force to overwrite)"
        )
    write_manifest(mpath, manifest)


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ModelResolveError(f"review manifest not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ModelResolveError(f"review manifest root must be a mapping: {path}")
    return data


def resolve_job(
    *,
    task_dir: Path,
    review_stage: str,
    round_num: int,
    agent: str | None,
    synthesis: bool,
    policy_path: Path,
    targets: dict[str, Any],
    preset_cfg: dict[str, Any],
) -> dict[str, Any]:
    state = load_task_state(task_dir)
    preset = get_review_depth_preset(state, task_dir)
    if synthesis:
        action = resolve_synthesis_action(
            review_stage=review_stage, preset_cfg=preset_cfg
        )
        output = "synthesis.md"
        job_agent = "synthesis"
    else:
        if not agent:
            raise ModelResolveError("--agent is required unless --synthesis is set")
        job_agent = validate_reviewer_agent(agent, targets)
        action = reviewer_action(job_agent)
        output = reviewer_output_filename(job_agent)
    resolved = resolve_for_task(task_dir, policy_path=policy_path, action=action)
    rel_output = (
        Path("reviews") / review_stage / f"round_{round_num:02d}" / output
    ).as_posix()
    return {
        "review_stage": review_stage,
        "round": round_num,
        "agent": job_agent,
        "action": action,
        "role": resolved["role"],
        "hermes_profile": resolved["hermes_profile"],
        "reasoning_expected": resolved["reasoning_expected"],
        "review_depth_preset": preset,
        "output": rel_output,
        "record_state": False,
    }


def record_session_in_manifest(
    *,
    manifest_file: Path,
    agent: str | None,
    synthesis: bool,
    session_export: Path,
    targets: dict[str, Any],
) -> dict[str, Any]:
    manifest = load_manifest(manifest_file)
    summary = build_summary(load_session_export(session_export))
    session_id = summary.get("session_id") or ""
    if not isinstance(session_id, str) or not session_id.strip():
        raise ModelResolveError("session export missing session id")
    usage_evidence = (
        f"hermes sessions export --session-id {session_id.strip()}; "
        f"{format_usage_cost(summary)}"
    )
    if synthesis:
        block = manifest.get("synthesis")
        if not isinstance(block, dict):
            raise ModelResolveError("manifest missing synthesis block")
        key_label = "synthesis"
    else:
        if not agent:
            raise ModelResolveError("--agent is required unless --synthesis is set")
        job_agent = validate_reviewer_agent(agent, targets)
        reviewers = manifest.get("reviewers")
        if not isinstance(reviewers, dict) or job_agent not in reviewers:
            raise ModelResolveError(f"manifest has no reviewer entry for {job_agent!r}")
        block = reviewers[job_agent]
        key_label = job_agent
    if not isinstance(block, dict):
        raise ModelResolveError(f"manifest entry for {key_label!r} must be a mapping")
    block["session_id"] = session_id.strip()
    block["usage_evidence"] = usage_evidence
    write_manifest(manifest_file, manifest)
    return {
        "manifest": manifest_file.as_posix(),
        "updated": key_label,
        "session_id": session_id.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="dp_review_job.py")
    parser.add_argument(
        "--task-dir",
        required=True,
        help="Path to .hermes/tasks/<task-id>",
    )
    parser.add_argument(
        "--review-stage",
        required=True,
        help="Review stage key (e.g. plan, implementation_phase_01, final)",
    )
    parser.add_argument(
        "--round", type=int, required=True, help="Review round number NN"
    )
    parser.add_argument(
        "--agent",
        default=None,
        help="Reviewer agent name (e.g. architecture); omit when --synthesis",
    )
    parser.add_argument(
        "--synthesis",
        action="store_true",
        help="Resolve or record synthesis job instead of a reviewer agent",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to model_policy.yaml (default: bundled)",
    )
    parser.add_argument(
        "--review-targets",
        default=None,
        help="Path to review_targets.yaml (default: bundled)",
    )
    parser.add_argument(
        "--init-manifest",
        action="store_true",
        help="Write review_manifest.yaml skeleton for this round",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="With --init-manifest, overwrite an existing review_manifest.yaml",
    )
    parser.add_argument(
        "--record-session",
        action="store_true",
        help="Update manifest session_id/usage_evidence from --session-export",
    )
    parser.add_argument(
        "--session-export",
        default=None,
        help="Path to hermes sessions export JSONL (required with --record-session)",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print resolved job JSON on stdout (default when not init/record)",
    )
    args = parser.parse_args()

    if args.agent and args.synthesis:
        print(
            "dp_review_job.py: use only one of --agent and --synthesis", file=sys.stderr
        )
        return 2
    if args.force and not args.init_manifest:
        print("dp_review_job.py: --force requires --init-manifest", file=sys.stderr)
        return 2

    try:
        if args.round < 1:
            raise ValueError("--round must be >= 1")

        task_dir = Path(args.task_dir).resolve()
        policy_path = (
            Path(args.policy).resolve() if args.policy else default_policy_path()
        )
        targets_path = (
            Path(args.review_targets).resolve()
            if args.review_targets
            else default_review_targets_path()
        )
        validate_policy(load_yaml(policy_path))
        targets = load_review_targets(targets_path)
        state = load_task_state(task_dir)
        preset = get_review_depth_preset(state, task_dir)
        preset_cfg = targets["presets"].get(preset)
        if not isinstance(preset_cfg, dict):
            raise ModelResolveError(f"preset {preset!r} missing in {targets_path.name}")
        review_stage = args.review_stage.strip()
        round_num = args.round
        mpath = manifest_path(task_dir, review_stage, round_num)

        if args.init_manifest:
            required = preset_cfg.get("required_reviewers")
            if not isinstance(required, list) or not required:
                raise ModelResolveError(
                    f"preset {preset!r} missing required_reviewers in {targets_path.name}"
                )
            synthesis_action = resolve_synthesis_action(
                review_stage=review_stage, preset_cfg=preset_cfg
            )
            manifest = build_manifest_skeleton(
                review_stage=review_stage,
                round_num=round_num,
                preset=preset,
                required_reviewers=[str(a) for a in required],
                synthesis_action=synthesis_action,
                policy_path=policy_path,
                task_dir=task_dir,
                targets=targets,
            )
            init_manifest_file(mpath=mpath, force=args.force, manifest=manifest)
            print(
                json.dumps(
                    {
                        "manifest": mpath.as_posix(),
                        "preset": preset,
                        "synthesis_action": synthesis_action,
                    },
                    indent=2,
                )
            )
            return 0

        if args.record_session:
            if not args.session_export:
                raise ModelResolveError("--record-session requires --session-export")
            result = record_session_in_manifest(
                manifest_file=mpath,
                agent=args.agent,
                synthesis=args.synthesis,
                session_export=Path(args.session_export),
                targets=targets,
            )
            print(json.dumps(result, indent=2, ensure_ascii=True))
            return 0

        if not args.agent and not args.synthesis:
            raise ModelResolveError(
                "specify --agent <name> or --synthesis for job resolution"
            )
        job = resolve_job(
            task_dir=task_dir,
            review_stage=review_stage,
            round_num=round_num,
            agent=args.agent,
            synthesis=args.synthesis,
            policy_path=policy_path,
            targets=targets,
            preset_cfg=preset_cfg,
        )
        print(json.dumps(job, indent=2, ensure_ascii=True))
        return 0
    except (ModelResolveError, OSError, ValueError) as exc:
        print(f"dp_review_job.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
