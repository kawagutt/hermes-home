#!/usr/bin/env python3
"""Unit tests for check_helper_env.py."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_helper_env.py"


class TestCheckHelperEnv(unittest.TestCase):
    def test_check_helper_env_exits_zero(self) -> None:
        r = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
