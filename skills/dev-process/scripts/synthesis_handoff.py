#!/usr/bin/env python3
"""Validate review synthesis.md blocking-finding handoff quality."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

VALID_OWNERS = frozenset(
    {"spec", "plan", "test", "implementation", "human", "artifact"}
)
PROCEED_RECOMMENDATION = "proceed"
PLACEHOLDER_RE = re.compile(
    r"^(?:…|\.\.\.|\.{3}|-+|—|–|ー|n/?a|none|tbd|todo|\s*)$",
    re.IGNORECASE,
)
RE_REVIEW_OK = re.compile(
    r"^(?:no|yes\s*[-—:]\s*.+review.*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BlockingRow:
    cells: tuple[str, ...]


def _is_placeholder(value: str) -> bool:
    return not value.strip() or bool(PLACEHOLDER_RE.match(value.strip()))


def _section_slice(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## ") and lines[j].strip() != heading:
            end = j
            break
    return "\n".join(lines[start:end])


def parse_recommendation_checked(text: str) -> list[str]:
    block = _section_slice(text, "## Recommendation")
    checked: list[str] = []
    for line in block.splitlines():
        m = re.match(r"^\s*-\s*\[(x|X)\]\s*(.+?)\s*$", line)
        if m:
            checked.append(m.group(2).strip())
    return checked


def _normalize_recommendation_label(label: str) -> str:
    return label.strip().lower()


def recommendation_requires_rework(text: str) -> bool:
    """True unless exactly one checked label is ``Proceed`` (template wording)."""
    checked = parse_recommendation_checked(text)
    if len(checked) != 1:
        return len(checked) > 1
    return _normalize_recommendation_label(checked[0]) != PROCEED_RECOMMENDATION


def _split_table_row(line: str) -> list[str]:
    raw = line.strip()
    if not raw.startswith("|"):
        return []
    parts = [p.strip() for p in raw.strip("|").split("|")]
    return parts


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells)


def _row_is_sentinel(cells: list[str]) -> bool:
    return all(c in ("—", "–", "-") for c in cells)


def parse_blocking_table(text: str) -> list[BlockingRow]:
    block = _section_slice(text, "## Rework owner (blocking findings)")
    if not block:
        block = _section_slice(text, "## Rework owner")
    rows: list[BlockingRow] = []
    header_seen = False
    for line in block.splitlines():
        cells = _split_table_row(line)
        if not cells:
            continue
        if _is_separator_row(cells):
            header_seen = True
            continue
        if not header_seen:
            header_seen = True
            continue
        if _row_is_sentinel(cells):
            continue
        if all(_is_placeholder(c) for c in cells):
            continue
        rows.append(BlockingRow(cells=tuple(cells)))
    return rows


def _cell(row: BlockingRow, index: int) -> str:
    if index < len(row.cells):
        return row.cells[index].strip()
    return ""


def _normalize_owner(owner_raw: str) -> str:
    return owner_raw.strip().strip("`").lower()


def _validate_blocking_row(
    row: BlockingRow, row_num: int, *, require_full_handoff: bool
) -> list[str]:
    errors: list[str] = []
    n = len(row.cells)
    if require_full_handoff and n < 6:
        errors.append(
            f"blocking row {row_num}: expected 6 columns "
            f"(ID | Summary | Owner | Exact file/section | Required action | Re-review); got {n}"
        )
        return errors
    if n < 4:
        errors.append(f"blocking row {row_num}: expected at least 4 columns (got {n})")
        return errors

    id_source = _cell(row, 0)
    summary = _cell(row, 1)
    owner_raw = _cell(row, 2)
    owner = _normalize_owner(owner_raw)

    if _is_placeholder(id_source):
        errors.append(f"blocking row {row_num}: missing ID source")
    if _is_placeholder(summary):
        errors.append(f"blocking row {row_num}: missing summary")

    if owner not in VALID_OWNERS:
        errors.append(
            f"blocking row {row_num}: invalid owner {owner_raw!r} "
            f"(expected exactly one of: {', '.join(sorted(VALID_OWNERS))})"
        )

    if n >= 6:
        exact = _cell(row, 3)
        action = _cell(row, 4)
        rereview = _cell(row, 5)
    else:
        exact = ""
        action = _cell(row, 3)
        rereview = ""

    if require_full_handoff or n >= 6:
        if _is_placeholder(exact):
            errors.append(
                f"blocking row {row_num}: missing exact file/section "
                "(path, artifact id, or spec/plan section)"
            )
    if _is_placeholder(action):
        errors.append(
            f"blocking row {row_num}: missing required action "
            "(concrete edit or command for the owner stage)"
        )
    if require_full_handoff or n >= 6:
        if _is_placeholder(rereview):
            errors.append(
                f"blocking row {row_num}: missing re-review required "
                "(yes — <stage> review, or no)"
            )
        elif not RE_REVIEW_OK.match(rereview):
            errors.append(
                f"blocking row {row_num}: re-review required must be "
                f"'no' or 'yes — <stage> review' (got {rereview!r})"
            )
    return errors


def validate_synthesis_handoff(text: str) -> list[str]:
    """Return human-readable validation errors (empty if OK)."""
    errors: list[str] = []
    stripped = text.strip()
    if not stripped:
        return ["synthesis is empty"]
    if stripped.startswith("# Synthesis placeholder"):
        return ["synthesis is still a placeholder"]
    if "## Recommendation" not in text:
        errors.append("missing ## Recommendation section")
        return errors

    checked = parse_recommendation_checked(text)
    if not checked:
        errors.append(
            "no recommendation selected (check exactly one - [x] under ## Recommendation)"
        )
    elif len(checked) != 1:
        errors.append(
            f"expected exactly one recommendation checkbox, got {len(checked)}: {checked!r}"
        )

    rework = recommendation_requires_rework(text)
    rows = parse_blocking_table(text)

    if rework:
        if not rows:
            errors.append(
                "rework/stop recommendation requires at least one blocking finding row "
                "in ## Rework owner (blocking findings)"
            )
        for i, row in enumerate(rows, 1):
            errors.extend(_validate_blocking_row(row, i, require_full_handoff=True))
    elif rows:
        errors.append(
            "Proceed recommendation must not include blocking finding rows "
            "(use a single sentinel row of — or leave the table empty)"
        )

    return errors


def synthesis_is_complete(path: Path) -> tuple[bool, list[str]]:
    if not path.is_file():
        return False, ["synthesis file missing"]
    text = path.read_text(encoding="utf-8")
    errors = validate_synthesis_handoff(text)
    return (len(errors) == 0, errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "synthesis",
        type=Path,
        help="Path to reviews/<stage>/round_NN/synthesis.md",
    )
    args = parser.parse_args()
    ok, errors = synthesis_is_complete(args.synthesis)
    if ok:
        print(f"OK {args.synthesis}")
        return 0
    print(f"ERROR {args.synthesis}", file=sys.stderr)
    for msg in errors:
        print(f"  - {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
