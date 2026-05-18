#!/usr/bin/env python3
"""Create or complete a dev-process review round directory."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


PLACEHOLDER_PREFIX = "# Synthesis placeholder"


def load_state(task: Path) -> dict:
    with (task / "state.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_state(task: Path, state: dict) -> None:
    with (task / "state.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False, allow_unicode=True)


def next_round(state: dict, stage: str) -> int:
    rounds = state.setdefault("review_rounds", {})
    return int(rounds.get(stage, 0) or 0) + 1


def round_rel(stage: str, number: int) -> Path:
    return Path("reviews") / stage / f"round_{number:02d}"


def synthesis_is_complete(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return False
    if text.startswith(PLACEHOLDER_PREFIX):
        return False
    return "## Recommendation" in text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Path to .hermes/tasks/<task-id>")
    parser.add_argument(
        "stage", help="Review stage key, e.g. plan or implementation_phase_01"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="Print next round without writing"
    )
    mode.add_argument(
        "--create",
        action="store_true",
        help="Create the next review round directory only",
    )
    mode.add_argument(
        "--finish",
        action="store_true",
        help="Mark an existing completed round as latest in state.yaml",
    )
    parser.add_argument(
        "--round",
        type=int,
        dest="round_number",
        help="Round number for --finish; defaults to next incomplete round",
    )
    args = parser.parse_args()

    task = Path(args.task)
    state = load_state(task)
    number = args.round_number or next_round(state, args.stage)
    rel_dir = round_rel(args.stage, number)
    abs_dir = task / rel_dir

    if args.dry_run or not (args.create or args.finish):
        print(f"DRY-RUN next {args.stage} review round: {rel_dir}")
        return 0

    if args.create:
        if abs_dir.exists():
            print(f"ERROR review round already exists: {rel_dir}")
            return 1
        abs_dir.mkdir(parents=True)
        print(f"CREATED {rel_dir}")
        print("state.yaml not updated; run --finish after real synthesis is complete")
        return 0

    synthesis_rel = rel_dir / "synthesis.md"
    synthesis_abs = task / synthesis_rel
    if not synthesis_is_complete(synthesis_abs):
        print(f"ERROR synthesis is missing or appears incomplete: {synthesis_rel}")
        return 1

    rounds = state.setdefault("review_rounds", {})
    latest = state.setdefault("latest_reviews", {})
    previous = int(rounds.get(args.stage, 0) or 0)
    if number != previous + 1:
        print(
            f"ERROR cannot finish round_{number:02d}; expected next completed round is round_{previous + 1:02d}"
        )
        return 1
    rounds[args.stage] = number
    latest[args.stage] = synthesis_rel.as_posix()
    write_state(task, state)
    print(f"FINISHED {rel_dir}")
    print(f"UPDATED review_rounds.{args.stage}={number}")
    print(f"UPDATED latest_reviews.{args.stage}={synthesis_rel.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
