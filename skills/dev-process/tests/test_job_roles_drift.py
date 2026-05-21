"""ROLE_PROFILES must match config/model_policy.yaml Hermes profile names."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from job_roles import ROLE_PROFILES  # noqa: E402

POLICY = ROOT / "config" / "model_policy.yaml"

ROLE_TO_POLICY_KEY = {
    "spec": "strong_reasoning",
    "plan": "strong_reasoning",
    "test": "code_main",
    "implementation": "code_main",
    "review_synthesis": "strong_reasoning",
    "review_worker": "code_main",
    "final_review": "strong_reasoning",
    "final_summary": "strong_reasoning",
}


def test_role_profiles_match_model_policy() -> None:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    profiles = policy["profiles"]
    for role, hp in ROLE_PROFILES.items():
        key = ROLE_TO_POLICY_KEY[role]
        assert profiles[key] == hp, f"{role}: {hp!r} != profiles[{key!r}]"
