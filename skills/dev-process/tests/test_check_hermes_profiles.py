"""Tests for check_hermes_profiles.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_hermes_profiles import (  # noqa: E402
    check_hermes_profiles,
    load_expected_reasoning_efforts,
    required_profile_names,
    resolve_hermes_home,
    run_check,
)
from model_resolve import default_policy_path, load_yaml, validate_policy  # noqa: E402

SCRIPT = SCRIPTS / "check_hermes_profiles.py"
EXPECTATIONS = SCRIPTS.parent / "config" / "hermes_profile_expectations.yaml"
EXAMPLES = SCRIPTS.parent / "examples" / "hermes-profiles.dp.yaml"


def _write_profile(hermes_home: Path, name: str, effort: str) -> None:
    profile_dir = hermes_home / "profiles" / name
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "config.yaml").write_text(
        f"agent:\n  reasoning_effort: {effort}\n",
        encoding="utf-8",
    )


def test_load_expected_reasoning_efforts() -> None:
    expected = load_expected_reasoning_efforts(EXPECTATIONS)
    assert expected["dp-strong"] == "high"
    assert expected["dp-review"] == "medium"
    assert expected["dp-code"] == "medium"
    assert expected["dp-cheap"] == "low"


def test_required_profile_names_from_policy() -> None:
    policy = validate_policy(load_yaml(default_policy_path()))
    names = required_profile_names(policy)
    assert names == {"dp-strong", "dp-review", "dp-code", "dp-cheap"}


def test_check_profiles_ok(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    policy = validate_policy(load_yaml(default_policy_path()))
    expected = load_expected_reasoning_efforts(EXPECTATIONS)
    for name, effort in expected.items():
        _write_profile(home, name, effort)
    issues = check_hermes_profiles(
        hermes_home=home,
        policy=policy,
        expected_efforts=expected,
        strict=False,
        skip_if_no_profiles_dir=False,
        expectations_label="expectations",
    )
    assert issues == []


def test_check_profiles_mismatch_non_strict_warning(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    policy = validate_policy(load_yaml(default_policy_path()))
    expected = load_expected_reasoning_efforts(EXPECTATIONS)
    for name, effort in expected.items():
        _write_profile(home, name, effort)
    _write_profile(home, "dp-strong", "low")
    issues = check_hermes_profiles(
        hermes_home=home,
        policy=policy,
        expected_efforts=expected,
        strict=False,
        skip_if_no_profiles_dir=False,
    )
    assert len(issues) == 1
    assert issues[0].level == "warning"
    assert "dp-strong" in issues[0].message


def test_check_profiles_mismatch_strict_error(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    policy = validate_policy(load_yaml(default_policy_path()))
    expected = load_expected_reasoning_efforts(EXPECTATIONS)
    for name, effort in expected.items():
        _write_profile(home, name, effort)
    _write_profile(home, "dp-code", "high")
    issues = check_hermes_profiles(
        hermes_home=home,
        policy=policy,
        expected_efforts=expected,
        strict=True,
        skip_if_no_profiles_dir=False,
    )
    assert any(i.level == "error" and "dp-code" in i.message for i in issues)


def test_run_check_missing_profiles_dir_warns(tmp_path: Path) -> None:
    code, issues = run_check(
        hermes_home=tmp_path / "empty",
        strict=False,
        skip_if_no_profiles_dir=True,
    )
    assert code == 0
    assert issues and issues[0].level == "warning"


def test_run_check_strict_missing_profiles_dir_fails(tmp_path: Path) -> None:
    code, issues = run_check(
        hermes_home=tmp_path / "missing",
        strict=True,
        skip_if_no_profiles_dir=True,
    )
    assert code == 1
    assert any(i.level == "error" for i in issues)


def test_missing_expected_effort_strict_error(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    policy = validate_policy(load_yaml(default_policy_path()))
    partial = tmp_path / "partial_expectations.yaml"
    partial.write_text(
        "profiles:\n  dp-strong:\n    reasoning_effort: high\n",
        encoding="utf-8",
    )
    expected = load_expected_reasoning_efforts(partial)
    _write_profile(home, "dp-strong", "high")
    issues = check_hermes_profiles(
        hermes_home=home,
        policy=policy,
        expected_efforts=expected,
        strict=True,
        skip_if_no_profiles_dir=False,
    )
    assert any(
        i.level == "error" and "dp-review" in i.message for i in issues
    )


def test_run_check_strict_missing_profile(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    (home / "profiles").mkdir(parents=True)
    code, issues = run_check(
        hermes_home=home,
        strict=True,
        skip_if_no_profiles_dir=False,
    )
    assert code == 1
    assert any(i.level == "error" for i in issues)


def test_cli_ok(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    expected = load_expected_reasoning_efforts(EXPECTATIONS)
    for name, effort in expected.items():
        _write_profile(home, name, effort)
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--hermes-home", str(home), "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "OK" in r.stdout


def test_resolve_hermes_home_explicit(tmp_path: Path) -> None:
    assert resolve_hermes_home(str(tmp_path)) == tmp_path.resolve()
