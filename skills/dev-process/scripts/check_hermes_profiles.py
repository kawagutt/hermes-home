#!/usr/bin/env python3
"""Validate dev-process Hermes profile configs against expected reasoning_effort tiers."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # noqa: F401
except ImportError:
    print(
        "check_hermes_profiles.py: PyYAML is required (pip install pyyaml)",
        file=sys.stderr,
    )
    raise SystemExit(2) from None

from model_resolve import default_policy_path, load_yaml, validate_policy


@dataclass(frozen=True)
class ProfileIssue:
    level: str  # "error" | "warning"
    message: str


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def default_expectations_path() -> Path:
    return _script_dir().parent / "config" / "hermes_profile_expectations.yaml"


def resolve_hermes_home(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".hermes").resolve()


def load_expected_reasoning_efforts(expectations_path: Path) -> dict[str, str]:
    if not expectations_path.is_file():
        raise FileNotFoundError(f"expectations file not found: {expectations_path}")
    data = load_yaml(expectations_path)
    if not isinstance(data, dict):
        raise ValueError(f"{expectations_path}: root must be a mapping")

    profiles = data.get("profiles")
    if isinstance(profiles, dict) and profiles:
        expected: dict[str, str] = {}
        for name, entry in profiles.items():
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(entry, dict):
                raise ValueError(
                    f"{expectations_path}: profiles[{name!r}] must be a mapping"
                )
            effort = entry.get("reasoning_effort")
            if not isinstance(effort, str) or not effort.strip():
                raise ValueError(
                    f"{expectations_path}: profiles[{name!r}] "
                    "missing reasoning_effort"
                )
            expected[name.strip()] = effort.strip().lower()
        return expected

    # Legacy: examples/hermes-profiles.dp.yaml profile_config_snippets
    snippets = data.get("profile_config_snippets")
    if not isinstance(snippets, dict) or not snippets:
        raise ValueError(
            f"{expectations_path}: missing profiles or profile_config_snippets"
        )
    expected = {}
    for name, snippet in snippets.items():
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(snippet, dict):
            raise ValueError(
                f"{expectations_path}: snippet for {name!r} must be a mapping"
            )
        agent = snippet.get("agent")
        if not isinstance(agent, dict):
            raise ValueError(
                f"{expectations_path}: profile_config_snippets[{name!r}].agent missing"
            )
        effort = agent.get("reasoning_effort")
        if not isinstance(effort, str) or not effort.strip():
            raise ValueError(
                f"{expectations_path}: profile_config_snippets[{name!r}] "
                "missing agent.reasoning_effort"
            )
        expected[name.strip()] = effort.strip().lower()
    return expected


def required_profile_names(policy: dict[str, Any]) -> set[str]:
    profiles = policy.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("policy profiles must be a mapping")
    names: set[str] = set()
    for hp in profiles.values():
        if isinstance(hp, str) and hp.strip():
            names.add(hp.strip())
    return names


def read_profile_reasoning_effort(config_path: Path) -> tuple[str | None, str | None]:
    """Return (effort_lower, error_message)."""
    if not config_path.is_file():
        return None, f"missing config: {config_path}"
    try:
        data = load_yaml(config_path)
    except Exception as exc:
        return None, f"failed to read {config_path}: {exc}"
    if not isinstance(data, dict):
        return None, f"malformed {config_path}: root not a mapping"
    agent = data.get("agent")
    if not isinstance(agent, dict):
        return None, f"missing agent section in {config_path}"
    effort = agent.get("reasoning_effort")
    if effort is None or (isinstance(effort, str) and not effort.strip()):
        return None, f"missing agent.reasoning_effort in {config_path}"
    if not isinstance(effort, str):
        return None, f"invalid agent.reasoning_effort in {config_path}"
    return effort.strip().lower(), None


def check_hermes_profiles(
    *,
    hermes_home: Path,
    policy: dict[str, Any],
    expected_efforts: dict[str, str],
    strict: bool = False,
    skip_if_no_profiles_dir: bool = True,
    expectations_label: str = "expectations",
) -> list[ProfileIssue]:
    issues: list[ProfileIssue] = []
    required = required_profile_names(policy)
    profiles_root = hermes_home / "profiles"

    if not profiles_root.is_dir():
        msg = (
            f"Hermes profiles directory not found: {profiles_root} "
            f"(HERMES_HOME={hermes_home})"
        )
        if skip_if_no_profiles_dir and not strict:
            issues.append(ProfileIssue("warning", f"skip: {msg}"))
        else:
            issues.append(ProfileIssue("error", msg))
        return issues

    for profile_name in sorted(required):
        expected = expected_efforts.get(profile_name)
        if expected is None:
            level = "error" if strict else "warning"
            issues.append(
                ProfileIssue(
                    level,
                    f"no expected reasoning_effort for policy profile "
                    f"{profile_name!r} in {expectations_label} (skipped)",
                )
            )
            continue

        config_path = profiles_root / profile_name / "config.yaml"
        actual, err = read_profile_reasoning_effort(config_path)
        if err:
            level = "error" if strict else "warning"
            issues.append(ProfileIssue(level, f"{profile_name}: {err}"))
            continue
        assert actual is not None
        if actual != expected:
            level = "error" if strict else "warning"
            issues.append(
                ProfileIssue(
                    level,
                    f"{profile_name}: agent.reasoning_effort={actual!r}, "
                    f"expected {expected!r} "
                    f"({config_path})",
                )
            )

    return issues


def format_issues(issues: list[ProfileIssue]) -> str:
    return "\n".join(f"{i.level}: {i.message}" for i in issues)


def run_check(
    *,
    hermes_home: Path | None = None,
    policy_path: Path | None = None,
    expectations_path: Path | None = None,
    strict: bool = False,
    skip_if_no_profiles_dir: bool = True,
) -> tuple[int, list[ProfileIssue]]:
    home = hermes_home or resolve_hermes_home(None)
    policy_file = policy_path or default_policy_path()
    expectations_file = expectations_path or default_expectations_path()

    try:
        policy = validate_policy(load_yaml(policy_file))
        expected = load_expected_reasoning_efforts(expectations_file)
    except Exception as exc:
        print(f"check_hermes_profiles.py: {exc}", file=sys.stderr)
        return 2, []

    issues = check_hermes_profiles(
        hermes_home=home,
        policy=policy,
        expected_efforts=expected,
        strict=strict,
        skip_if_no_profiles_dir=skip_if_no_profiles_dir,
        expectations_label=str(expectations_file),
    )

    errors = [i for i in issues if i.level == "error"]

    if issues:
        print(format_issues(issues), file=sys.stderr)

    if errors:
        return 1, issues
    return 0, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hermes-home",
        default=None,
        help="Hermes home directory (default: $HERMES_HOME or ~/.hermes)",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to model_policy.yaml (default: bundled)",
    )
    parser.add_argument(
        "--expectations",
        default=None,
        help=(
            "Path to hermes_profile_expectations.yaml "
            "(default: bundled config/hermes_profile_expectations.yaml)"
        ),
    )
    parser.add_argument(
        "--examples",
        default=None,
        help="Deprecated alias for --expectations (legacy examples file)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on missing profiles directory, missing expectations, or mismatch",
    )
    parser.add_argument(
        "--no-skip-missing",
        action="store_true",
        help=(
            "In non-strict mode, treat a missing profiles/ directory as error "
            "instead of a skip warning"
        ),
    )
    args = parser.parse_args()

    home = resolve_hermes_home(args.hermes_home)
    policy_path = Path(args.policy).resolve() if args.policy else None
    if args.examples and args.expectations:
        print(
            "check_hermes_profiles.py: use only one of --expectations or --examples",
            file=sys.stderr,
        )
        return 2
    expectations_arg = args.expectations or args.examples
    expectations_path = Path(expectations_arg).resolve() if expectations_arg else None

    code, issues = run_check(
        hermes_home=home,
        policy_path=policy_path,
        expectations_path=expectations_path,
        strict=args.strict,
        skip_if_no_profiles_dir=not args.no_skip_missing,
    )
    if code == 0 and not issues:
        print(f"OK Hermes profiles under {home / 'profiles'}")
    elif code == 0 and issues:
        print(f"OK Hermes profiles (warnings only) under {home / 'profiles'}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
