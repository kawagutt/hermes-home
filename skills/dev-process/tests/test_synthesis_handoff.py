"""Tests for synthesis_handoff.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from synthesis_handoff import (  # noqa: E402
    recommendation_requires_rework,
    validate_synthesis_handoff,
)

PROCEED_ONLY = """\
## Recommendation

- [x] Proceed
- [ ] Rework implementation

**One-line rationale:** OK

## Rework owner (blocking findings)

| ID source | Summary | Owner | Exact file/section | Required action | Re-review required |
|-----------|---------|-------|--------------------|-----------------|------------------|
| — | — | — | — | — | — |
"""

REWORK_INCOMPLETE = """\
## Recommendation

- [ ] Proceed
- [x] Rework plan

**One-line rationale:** Plan gap

## Rework owner (blocking findings)

| ID source | Summary | Owner | Exact file/section | Required action | Re-review required |
|-----------|---------|-------|--------------------|-----------------|------------------|
| F1 | missing phase sizing | plan | | fix plan | |
"""

REWORK_COMPLETE = """\
## Recommendation

- [x] Rework implementation

**One-line rationale:** Code gap

## Rework owner (blocking findings)

| ID source | Summary | Owner | Exact file/section | Required action | Re-review required |
|-----------|---------|-------|--------------------|-----------------|------------------|
| F2 diff | null deref | implementation | `src/foo.py:42` | Add guard before use | yes — implementation_phase_01 review |
"""


def test_proceed_only_passes() -> None:
    assert not recommendation_requires_rework(PROCEED_ONLY)
    assert validate_synthesis_handoff(PROCEED_ONLY) == []


def test_proceed_label_must_match_exactly() -> None:
    text = """\
## Recommendation
- [x] Proceed with artifact repair
## Rework owner (blocking findings)
| ID | Summary | Owner | Exact file/section | Required action | Re-review required |
|----|---------|-------|--------------------|-----------------|------------------|
| — | — | — | — | — | — |
"""
    assert recommendation_requires_rework(text)


def test_rework_requires_full_blocking_row() -> None:
    assert recommendation_requires_rework(REWORK_INCOMPLETE)
    errs = validate_synthesis_handoff(REWORK_INCOMPLETE)
    assert any("exact file/section" in e for e in errs)
    assert any("re-review required" in e for e in errs)


def test_rework_complete_passes() -> None:
    assert recommendation_requires_rework(REWORK_COMPLETE)
    assert validate_synthesis_handoff(REWORK_COMPLETE) == []


def test_rework_without_rows_fails() -> None:
    text = """\
## Recommendation
- [x] Rework tests
## Rework owner (blocking findings)
| ID | Summary | Owner | Exact file/section | Required action | Re-review required |
|----|---------|-------|--------------------|-----------------|------------------|
"""
    errs = validate_synthesis_handoff(text)
    assert any("at least one blocking" in e for e in errs)


def test_owner_slash_list_rejected() -> None:
    text = """\
## Recommendation
- [x] Rework plan
## Rework owner (blocking findings)
| ID | Summary | Owner | Exact file/section | Required action | Re-review required |
|----|---------|-------|--------------------|-----------------|------------------|
| F1 | gap | spec / plan / test | artifacts.plan | rewrite | yes — plan review |
"""
    errs = validate_synthesis_handoff(text)
    assert any("invalid owner" in e and "spec / plan" in e for e in errs)


def test_exact_em_dash_rejected() -> None:
    text = """\
## Recommendation
- [x] Rework plan
## Rework owner (blocking findings)
| ID | Summary | Owner | Exact file/section | Required action | Re-review required |
|----|---------|-------|--------------------|-----------------|------------------|
| F1 | gap | plan | — | update phases | yes — plan review |
"""
    errs = validate_synthesis_handoff(text)
    assert any("exact file/section" in e for e in errs)


def test_rereview_yes_only_rejected() -> None:
    text = """\
## Recommendation
- [x] Rework plan
## Rework owner (blocking findings)
| ID | Summary | Owner | Exact file/section | Required action | Re-review required |
|----|---------|-------|--------------------|-----------------|------------------|
| F1 | gap | plan | artifacts.plan §2 | rewrite | yes |
"""
    errs = validate_synthesis_handoff(text)
    assert any("re-review required" in e for e in errs)


def test_synthesis_handoff_cli_rejects_incomplete(tmp_path: Path) -> None:
    path = tmp_path / "synthesis.md"
    path.write_text(REWORK_INCOMPLETE, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "synthesis_handoff.py"), str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert r.returncode == 1
    assert "ERROR" in r.stderr


def test_proceed_with_none_row_rejected() -> None:
    text = """\
## Recommendation
- [x] Proceed
## Rework owner (blocking findings)
| ID | Summary | Owner | Exact file/section | Required action | Re-review required |
|----|---------|-------|--------------------|-----------------|------------------|
| (none) | | | | | |
"""
    errs = validate_synthesis_handoff(text)
    assert any("Proceed recommendation must not include blocking" in e for e in errs)


def test_proceed_with_blocking_row_rejected() -> None:
    text = """\
## Recommendation
- [x] Proceed
## Rework owner (blocking findings)
| ID | Summary | Owner | Exact file/section | Required action | Re-review required |
|----|---------|-------|--------------------|-----------------|------------------|
| F1 | gap | plan | artifacts.plan | fix | no |
"""
    errs = validate_synthesis_handoff(text)
    assert any("Proceed recommendation must not include blocking" in e for e in errs)
