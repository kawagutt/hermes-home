"""Regression tests for dev-process v3 policy documentation.

These tests exercise documentation/policy invariants from the approved dev-process v3 plan.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Inline Markdown links: ](target) or ](target#frag) — skip URLs and same-file fragments.
_MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")


def strip_md_emphasis(text: str) -> str:
    """Remove common Markdown emphasis for substring policy checks."""
    return re.sub(r"\*+", "", text)


def read_rel(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def section_after_heading(heading: str, text: str) -> str:
    start = text.find(heading)
    assert start != -1, f"missing heading {heading!r}"
    after = text[start + len(heading) :].lstrip("\n")
    cut = after.find("\n## ")
    return after if cut == -1 else after[:cut]


def all_markdown() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*.md"))


def test_review_depth_has_single_canonical_preset_table() -> None:
    text = all_markdown()
    presets = read_rel("review/presets.md")
    # Canonical reviewer-requirements table lives only in presets.md; other SKILLs may mention "| Preset |" columns.
    assert presets.count("| Preset |") == 1
    assert "single source of truth" in text
    assert "externally observable product behavior" in text
    assert "public/user-visible behavior" not in text
    assert "`test_quality`, `synthesis`" not in presets
    assert "Synthesis is the merge step" in presets
    assert "Optional specialist reviewers" in presets


def test_standard_recipes_do_not_override_presets() -> None:
    review = read_rel("review/SKILL.md")
    assert (
        "single source of truth for preset reviewer requirements and synthesis rules"
        in review
    )
    assert "For `light` or `deep`, use [`presets.md`](presets.md)" in review
    assert "Do not treat this section as overriding" in review


def test_explicit_role_transition_preserves_review_independence() -> None:
    text = all_markdown()
    assert "Explicit role transition must not weaken review context isolation" in text
    assert (
        "but not ImplementationAgent chat rationale unless explicitly requested" in text
    )


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
    assert (
        "Do not stop solely because the next legal action belongs to another role"
        in text
    )
    assert "explicit role transition" in text
    assert "or a role boundary" not in text


def test_helper_readme_documents_dependencies_timeline_and_comment_policy() -> None:
    readme = read_rel("scripts/README.md")
    assert "PyYAML" in readme
    assert "Timeline precondition" in readme
    assert "Time | Stage | Action | Output" in readme
    assert "may drop YAML comments" in readme
    assert "`## Recommendation`" in readme


def test_orchestrator_human_gates_subsection_covers_required_decisions() -> None:
    skill = read_rel("SKILL.md")
    hg = section_after_heading("## Human gates", skill)
    assert "Required human decisions" in hg
    assert "one by one in chat" in hg
    assert "final approval" in hg
    assert "generic" in hg.lower()


def test_orchestrator_lines_do_not_imply_ok_after_summary_only() -> None:
    skill = read_rel("SKILL.md")
    needles = ("after the summary is provided", "after the concise japanese summary")
    tokens = (
        "Required human decisions",
        "one by one",
        "individually",
        "required decision items",
    )
    for i, line in enumerate(skill.splitlines(), start=1):
        lower = line.lower()
        if not any(n in lower for n in needles):
            continue
        assert any(
            t in line for t in tokens
        ), f"line {i} may imply OK after summary only: {line!r}"


def test_test_skill_matches_explicit_role_transition_policy() -> None:
    test_skill = read_rel("test/SKILL.md")
    assert "explicit role transition" in test_skill
    assert "Do not silently change role" in test_skill
    assert (
        "Do not stop merely because the test stage boundary or role boundary was reached"
        in test_skill
    )


def test_safe_deterministic_helper_execution_documented() -> None:
    validation_skill = read_rel("validation/SKILL.md")
    assert "### Safe deterministic helper execution" in validation_skill
    assert "run-dp" in validation_skill
    assert "validate_state.py" in validation_skill
    assert "review_round.py" in validation_skill


def test_human_decision_prompt_template_exists_and_is_linked() -> None:
    prompt = read_rel("templates/human_decision_prompt.md")
    assert "one by one" in prompt
    assert "Final approval question" in prompt
    assert "Visibility rule" in prompt
    assert "numbered" in prompt.casefold()
    gate = read_rel("templates/human_spec_gate.md")
    assert "human_decision_prompt.md" in gate
    assert (
        read_rel("templates/final_human_gate.md").count("human_decision_prompt.md") >= 1
    )


def test_spec_skill_ties_ok_to_individual_decisions() -> None:
    spec = read_rel("spec/SKILL.md")
    assert "one by one in chat" in spec
    assert "Required human decisions" in spec


def test_japanese_summary_templates_require_individual_decisions_before_ok() -> None:
    for path in ("templates/spec_summary_ja.md", "templates/final_summary_ja.md"):
        text = read_rel(path)
        assert "Required human decisions" in text
        assert "個別" in text
        assert "最終承認" in text


def test_model_usage_review_pre_v4_plan_field() -> None:
    """Pre-v4 plan field; v4 uses jobs.yaml for all presets."""
    plan = read_rel("templates/plan.md")
    validation = read_rel("validation/SKILL.md")
    assert "Model usage record required?" in plan
    assert "jobs.yaml" in validation


def test_model_usage_warns_not_to_paste_raw_logs_and_is_stage_attribution_aid() -> None:
    model_usage = read_rel("templates/model_usage.md")
    validation = read_rel("validation/SKILL.md")
    assert "jobs.yaml" in model_usage
    assert "generated/" in model_usage
    assert "run-dp render" in model_usage
    assert "Do not edit by hand" in model_usage
    assert "run-dp job close" in validation


def test_primary_segment_boundary_completion_in_validation() -> None:
    validation = read_rel("validation/SKILL.md")
    plain = strip_md_emphasis(validation)
    assert "v4 Job Contract" in validation
    assert "hermes sessions export" in validation
    assert "run-dp job close" in validation
    assert "run-dp validate --strict" in validation
    assert "No waiver" in validation
    assert "before final" in plain or "final_human_gate" in plain


def test_model_usage_template_boundary_completion_and_dp_stage_boundary() -> None:
    model_usage = read_rel("templates/model_usage.md")
    assert "Generated from jobs.yaml" in model_usage
    assert "run-dp render model-usage" in model_usage
    assert "review_summary.md" in model_usage


def test_governance_waiver_scope_in_validation_and_model_usage() -> None:
    validation = strip_md_emphasis(read_rel("validation/SKILL.md"))
    model_usage = read_rel("templates/model_usage.md")
    assert "No waiver" in validation
    assert "review_manifest.yaml" not in model_usage or "review_summary" in model_usage
    assert "unknown" not in validation.lower() or "does not" in validation


def test_minimal_rules_preflight_vs_governance_canonical() -> None:
    validation = strip_md_emphasis(read_rel("validation/SKILL.md"))
    scripts_readme = read_rel("scripts/README.md")
    assert "### Minimal rules (orchestration)" in validation
    assert "run-dp validate" in validation
    assert "validate_state.py" in validation
    assert "run-dp" in scripts_readme
    assert "Job Contract" in scripts_readme


def test_minimal_rules_human_gate_timeline_not_required_on_approval() -> None:
    validation = strip_md_emphasis(read_rel("validation/SKILL.md"))
    human_gates = read_rel("human-gates/SKILL.md")
    assert "pending_human_gate" in validation
    assert "approved.*" in validation or "approved" in validation
    assert "reject/rework" in validation.lower()
    # Approval path in companion skill does not require timeline append.
    assert "validate_state.py" in human_gates
    assert "timeline" in human_gates.lower()
    assert (
        "record in timeline" in human_gates.lower()
        or "timeline," in human_gates.lower()
    )


def test_review_round_session_evidence_completion_checklist() -> None:
    review = read_rel("review/SKILL.md")
    assert "## v4 review jobs" in review
    assert "run-dp job start" in review
    assert "review_worker" in review
    assert "Pre-v4" in review
    assert "review_manifest.yaml" in review


def test_goal_links_primary_boundary_completion() -> None:
    goal = read_rel("goal/SKILL.md")
    assert "v4 Job Contract" in goal or "run-dp job" in goal
    assert "1 /goal = 1 job" in goal


def test_orchestrator_session_model_evidence_links() -> None:
    skill = read_rel("SKILL.md")
    assert "## Session and model evidence" in skill
    assert "v4 Job Contract" in skill or "jobs.yaml" in skill
    assert "Pre-v4" in skill or "pre-v4" in skill


def test_test_skill_links_session_evidence() -> None:
    test_skill = read_rel("test/SKILL.md")
    assert "v4" in test_skill
    assert "run-dp" in test_skill or "review jobs" in test_skill


def test_dp_hermes_strict_launch_default_documented() -> None:
    readme = read_rel("scripts/README.md")
    review = read_rel("review/SKILL.md")
    goal = read_rel("goal/SKILL.md")
    assert "run-dp" in readme
    assert "exits with code 2" in readme.lower() or "job start" in readme
    assert "run-dp job" in review or "v4" in review
    assert "run-dp" in goal or "v4" in goal


INVARIANT_REVIEWED_FINAL = (
    "reviewed.final == true does not imply approved.final_human_gate == true."
)
INVARIANT_PENDING_STOP = (
    'pending_human_gate != "" means the orchestrator must stop,\n'
    "even if latest review recommendation is Proceed."
)
INVARIANT_REVIEWED_SPEC = (
    "reviewed.spec == true does not imply approved.human_spec_gate == true."
)


def test_human_gate_invariants_verbatim_in_goal_and_orchestrator() -> None:
    goal = read_rel("goal/SKILL.md")
    skill = read_rel("SKILL.md")
    for doc in (goal, skill):
        assert INVARIANT_REVIEWED_FINAL in doc
        assert INVARIANT_PENDING_STOP in doc
        assert INVARIANT_REVIEWED_SPEC in doc


def test_goal_stops_when_pending_human_gate_nonempty() -> None:
    goal = read_rel("goal/SKILL.md")
    assert INVARIANT_PENDING_STOP in goal
    assert "If **`pending_human_gate`** is non-empty, **STOP** immediately" in goal
    assert "even when the latest review synthesis recommends **Proceed**" in goal


def test_orchestrator_canonical_human_gate_state_block() -> None:
    skill = read_rel("SKILL.md")
    hg = section_after_heading("## Human gates", skill)
    assert "review-pass marker" in hg
    assert "Synthesis may set reviewed.<key>: true only when" in hg
    assert "pending_human_gate is the authoritative signal" in hg
    assert "After any explicit human gate decision" in hg
    assert "If not approved" in hg and "rework stage" in hg


def test_orchestrator_gate_presenter_order_before_stop() -> None:
    skill = read_rel("SKILL.md")
    hg = section_after_heading("## Human gates", skill)
    assert "gate artifact" in hg.casefold()
    assert "pending_human_gate" in hg
    assert "gate_prompted" in hg
    assert "numbered" in hg.casefold()
    assert "STOP" in hg


def test_reviewed_keys_only_template_defined() -> None:
    state = read_rel("templates/state.yaml")
    skill = read_rel("SKILL.md")
    review = read_rel("review/SKILL.md")
    assert "reviewed.spec" in state
    assert "reviewed.plan" in state
    assert "reviewed.tests" in state
    assert "reviewed.final" in state
    assert "Do not invent" in state or "do not invent" in state.lower()
    combined = skill + review
    assert "implementation_phase" in combined
    assert "do not" in combined.lower() and "reviewed.*" in combined


def test_synthesis_proceed_only_sets_reviewed() -> None:
    synthesis = read_rel("review/agents/synthesis.md")
    lower = synthesis.lower()
    assert "review-pass marker" in synthesis
    assert "accepts the stage" in lower
    assert "Do **not** set **`approved.*`**" in synthesis
    assert "pending_human_gate" in synthesis
    assert "gate_prompted_at" in synthesis
    assert "Do **not** set `reviewed.*` on rework" in synthesis
    assert "synthesis must not set approved" in lower
    assert "may set approved" not in lower


def test_human_rejection_clears_pending_human_gate() -> None:
    skill = read_rel("SKILL.md")
    spec = read_rel("spec/SKILL.md")
    review = read_rel("review/SKILL.md")
    combined = skill + spec + review
    assert "clear" in combined.lower() and "pending_human_gate" in combined
    assert "not approved" in combined.lower() or "reject" in combined.lower()


def test_state_template_pending_human_gate_fields() -> None:
    state = read_rel("templates/state.yaml")
    assert "pending_human_gate:" in state
    assert "gate_prompted_at:" in state
    assert "human_spec_gate" in state
    assert "final_human_gate" in state


def test_approved_spec_not_in_canonical_state_template() -> None:
    state = read_rel("templates/state.yaml")
    approved_block = state.split("approved:", 1)[1].split("\nreviewed:", 1)[0]
    assert "human_spec_gate:" in approved_block
    assert "final_human_gate:" in approved_block
    assert "\n  spec:" not in approved_block and "  spec: false" not in approved_block


def test_final_human_gate_template_gate_status_and_no_misleading_phrases() -> None:
    text = read_rel("templates/final_human_gate.md")
    plain = strip_md_emphasis(text)
    assert "## Gate status" in text
    assert "reviewed.final" in text and "not mean" in plain.lower()
    assert "Final approval" in text and "pending" in text
    assert "Itemized decisions from upstream" in text
    assert "Final gate approval:" in text and "still required" in text
    assert "Required human decisions: None" not in text
    assert (
        "The task is ready for the human-controlled commit / merge / completion decision."
        not in text
    )
    assert "ready for the human-controlled" not in text


def test_human_spec_gate_template_gate_status_and_no_none_phrase() -> None:
    text = read_rel("templates/human_spec_gate.md")
    plain = strip_md_emphasis(text)
    assert "## Gate status" in text
    assert "reviewed.spec" in text and "not mean" in plain.lower()
    assert "Itemized decisions from upstream" in text
    assert "Spec gate approval:" in text and "still required" in text
    assert "Required human decisions: None" not in text
    assert "approval to proceed to plan" in text
    assert "before asking for final approval" not in text


def test_human_gates_companion_task3_pitfalls_and_approval_recording() -> None:
    hg = read_rel("human-gates/SKILL.md")
    assert "## Gate approval recording" in hg
    assert "pending_human_gate" in hg
    assert "Required human decisions: None" in hg
    assert "authoritative" in hg.lower() or "artifacts.human_spec_gate" in hg
    assert "Superseded" in hg or "superseded" in hg


def test_artifacts_skill_human_gate_authoritative_pointer() -> None:
    art = read_rel("artifacts/SKILL.md")
    assert "### Human gate artifacts" in art
    assert "artifacts.human_spec_gate" in art
    assert "artifacts.final_human_gate" in art
    assert "Authoritative" in art or "authoritative" in art
    assert "non-canonical history" in art.lower() or "history" in art.lower()
    assert "Superseded" in art
    assert "optional" in art.lower()
    assert "current bound" in art.lower()
    assert "in place" in art.lower()
    assert "solely because Approval checkboxes" in art
    assert "solely to add this marker" in art
    assert "Human gate files are not append-only" not in art


def test_plan_start_rule_uses_human_spec_gate_not_approved_spec() -> None:
    skill = read_rel("SKILL.md")
    goal = read_rel("goal/SKILL.md")
    spec = read_rel("spec/SKILL.md")
    combined = skill + goal + spec
    assert (
        "Plan may start only when:" in combined
        or "Plan must not start until:" in combined
    )
    assert "approved.human_spec_gate == true" in combined
    assert 'pending_human_gate == ""' in combined
    assert "reviewed.spec == true" in combined
    assert "Do not use `approved.spec`" in combined or "not `approved.spec`" in combined


def test_markdown_relative_links_resolve_under_dev_process_skill() -> None:
    """Fail if Markdown points to missing paths (catches ../../ typos vs skill layout)."""

    skipped_prefixes = ("http://", "https://", "mailto:", "tel:")

    for md_path in sorted(ROOT.rglob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        for m in _MD_LINK_RE.finditer(text):
            raw = m.group(1).strip()
            if any(raw.startswith(p) for p in skipped_prefixes):
                continue
            path_part = raw.partition("#")[0].strip()
            if not path_part:
                continue
            if path_part.startswith("<") and path_part.endswith(">"):
                path_part = path_part[1:-1].strip()
            candidate = (md_path.parent / path_part).resolve()
            assert (
                candidate.exists()
            ), f"{md_path.relative_to(ROOT)}: broken link ({raw!r}) -> {candidate}"
