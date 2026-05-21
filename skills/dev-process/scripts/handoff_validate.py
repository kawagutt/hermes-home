"""Validate v4 handoff markdown briefing files."""

from __future__ import annotations

import re
from pathlib import Path

HANDOFF_SECTIONS = (
    "## Approved facts",
    "## Artifact paths",
    "## Decisions",
    "## Open items",
)

MIN_HANDOFF_BODY_CHARS = 40


def normalize_handoff_in(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            s = item.strip()
            if s:
                out.append(s)
        return out
    raise ValueError(f"handoff_in must be a list or string, got {type(value).__name__}")


class HandoffValidationError(Exception):
    """Handoff file validation failure."""


def validate_handoff_markdown(path: Path, *, label: str) -> None:
    if not path.is_file():
        raise HandoffValidationError(f"{label} missing: {path}")
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if len(stripped) < MIN_HANDOFF_BODY_CHARS:
        raise HandoffValidationError(f"{label} is empty or too short: {path}")
    if "<!--" in stripped and "stub" in stripped.lower():
        raise HandoffValidationError(f"{label} still contains stub marker: {path}")

    for section in HANDOFF_SECTIONS:
        if section not in text:
            raise HandoffValidationError(f"{label} missing section {section!r}: {path}")

    for i, section in enumerate(HANDOFF_SECTIONS):
        start = text.find(section)
        if start < 0:
            continue
        body_start = start + len(section)
        if i + 1 < len(HANDOFF_SECTIONS):
            end = text.find(HANDOFF_SECTIONS[i + 1], body_start)
            body = text[body_start:end] if end >= 0 else text[body_start:]
        else:
            body = text[body_start:]
        body = re.sub(r"^#+\s.*$", "", body, flags=re.MULTILINE).strip()
        if len(body) < 8:
            raise HandoffValidationError(
                f"{label} section {section!r} has no substantive content: {path}"
            )
