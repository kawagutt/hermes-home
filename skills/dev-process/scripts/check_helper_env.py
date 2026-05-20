#!/usr/bin/env python3
"""Preflight dev-process helper environment (PyYAML, policy, CLI entrypoints)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # noqa: F401
except ImportError:
    print("check_helper_env.py: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2) from None

from model_resolve import default_policy_path, load_yaml, validate_policy


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _run_help(script: Path) -> None:
    r = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"{script.name} --help failed (exit {r.returncode}): {r.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to model_policy.yaml (default: bundled)",
    )
    args = parser.parse_args()

    scripts = _script_dir()
    policy_path = Path(args.policy).resolve() if args.policy else default_policy_path()

    try:
        validate_policy(load_yaml(policy_path))
        for name in (
            "dp_hermes.py",
            "dp_stage_boundary.py",
            "dp_review_job.py",
            "session_usage.py",
            "validate_state.py",
            "validate_model_governance.py",
        ):
            _run_help(scripts / name)
    except Exception as exc:
        print(f"check_helper_env.py: {exc}", file=sys.stderr)
        return 2

    print("OK dev-process helper environment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
