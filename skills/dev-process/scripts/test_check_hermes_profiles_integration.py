#!/usr/bin/env python3
"""Integration tests for check_helper_env.py --check-profiles."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
CHECK_HELPER = SCRIPTS / "check_helper_env.py"
EXPECTATIONS = SCRIPTS.parent / "config" / "hermes_profile_expectations.yaml"


def _write_profile(hermes_home: Path, name: str, effort: str) -> None:
    profile_dir = hermes_home / "profiles" / name
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "config.yaml").write_text(
        f"agent:\n  reasoning_effort: {effort}\n",
        encoding="utf-8",
    )


class TestCheckHelperEnvProfiles(unittest.TestCase):
    def test_check_profiles_via_helper_env(self) -> None:
        import yaml

        expected = yaml.safe_load(EXPECTATIONS.read_text(encoding="utf-8"))["profiles"]
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "hermes"
            for name, entry in expected.items():
                _write_profile(home, name, entry["reasoning_effort"])
            r = subprocess.run(
                [
                    sys.executable,
                    str(CHECK_HELPER),
                    "--check-profiles",
                    "--hermes-home",
                    str(home),
                    "--strict-profiles",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_check_helper_env_strict_missing_profiles_dir_fails(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "no_profiles_here"
            r = subprocess.run(
                [
                    sys.executable,
                    str(CHECK_HELPER),
                    "--check-profiles",
                    "--hermes-home",
                    str(home),
                    "--strict-profiles",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertIn("profiles directory", r.stderr.lower())


if __name__ == "__main__":
    unittest.main()
