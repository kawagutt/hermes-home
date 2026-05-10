"""Regression tests for dev-process v3 policy documentation.

These tests exercise documentation/policy invariants from the approved dev-process v3 plan.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def all_markdown() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*.md"))


def test_review_depth_has_single_canonical_preset_table() -> None:
    text = all_markdown()
    presets = read_rel("review/presets.md")
    assert text.count("| Preset |") == 1
    assert "single source of truth" in text
    assert "externally observable product behavior" in text
    assert "public/user-visible behavior" not in text
    assert "`test_quality`, `synthesis`" not in presets
    assert "Synthesis is the merge step" in presets
    assert "Optional specialist reviewers" in presets


def test_standard_recipes_do_not_override_presets() -> None:
    review = read_rel("review/SKILL.md")
    assert "single source of truth for preset reviewer requirements and synthesis rules" in review
    assert "For `light` or `deep`, use [`presets.md`](presets.md)" in review
    assert "Do not treat this section as overriding" in review


def test_explicit_role_transition_preserves_review_independence() -> None:
    text = all_markdown()
    assert "Explicit role transition must not weaken review context isolation" in text
    assert "but not ImplementationAgent chat rationale unless explicitly requested" in text


def test_review_depth_selection_uses_uncertainty_and_impact_not_diff_size() -> None:
    text = all_markdown()
    assert "remaining uncertainty" in text
    assert "impact if broken" in text
    assert "A smaller diff does not automatically mean `light`" in text
    assert "Documentation text-only changes do not count" in text


def test_human_gate_required_decisions_are_individual_not_generic_ok() -> None:
    text = all_markdown()
    assert "Required human decisions" in text
    assert "one by one in chat" in text
    assert "OK" in text and "final approval" in text
    assert "must not collapse multiple required human decisions" in text


def test_role_boundary_does_not_imply_human_confirmation() -> None:
    text = all_markdown()
    assert "Normal role/stage transitions" in text
    assert "do not require human confirmation" in text
    assert "explicit role transition" in text
    assert "not a human gate" in text


def test_nodeflow_is_explicitly_out_of_scope() -> None:
    text = all_markdown()
    assert "NodeFlow" in text
    assert "out of scope" in text


def test_role_boundary_is_not_an_automatic_stop_reason() -> None:
    text = all_markdown()
    assert "Role boundary is not an automatic stop condition" in text
    assert "Do not stop solely because the next legal action belongs to another role" in text
    assert "explicit role transition" in text
    assert "or a role boundary" not in text


def test_helper_readme_documents_dependencies_timeline_and_comment_policy() -> None:
    readme = read_rel("scripts/README.md")
    assert "PyYAML" in readme
    assert "Timeline precondition" in readme
    assert "Time | Stage | Action | Output" in readme
    assert "may drop YAML comments" in readme
    assert "`## Recommendation`" in readme
