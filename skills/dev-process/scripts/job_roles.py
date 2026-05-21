"""v4 Job Contract: fixed roles and Hermes profile mapping."""

from __future__ import annotations

ROLES = frozenset(
    {
        "spec",
        "plan",
        "test",
        "implementation",
        "review_worker",
        "review_synthesis",
        "final_review",
        "final_summary",
    }
)

ROLE_PROFILES: dict[str, str] = {
    "spec": "dp-strong",
    "plan": "dp-strong",
    "test": "dp-code",
    "implementation": "dp-code",
    "review_synthesis": "dp-strong",
    "review_worker": "dp-code",
    "final_review": "dp-strong",
    "final_summary": "dp-strong",
}

PRIMARY_ROLES = frozenset(
    {
        "spec",
        "plan",
        "test",
        "implementation",
        "final_review",
        "final_summary",
    }
)

REVIEW_ROLES = frozenset({"review_worker", "review_synthesis"})

INVALID_SESSION = frozenset({"unknown", "n/a", "na", "-", ""})


def profile_for_role(role: str) -> str:
    if role not in ROLE_PROFILES:
        raise ValueError(f"unknown role: {role!r}")
    return ROLE_PROFILES[role]


def default_stage_id(role: str, *, implementation_phase: str | None = None) -> str:
    if role == "implementation" and implementation_phase:
        return implementation_phase
    if role in ("final_review", "final_summary"):
        return role
    if role in ("review_worker", "review_synthesis"):
        return role
    return role


def validate_session_id(session_id: str) -> bool:
    """Non-blank, not a placeholder; format is validated by Hermes export at job close."""
    s = session_id.strip() if isinstance(session_id, str) else ""
    if not s:
        return False
    return s.lower() not in INVALID_SESSION
