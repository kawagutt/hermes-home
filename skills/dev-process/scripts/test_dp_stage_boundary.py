#!/usr/bin/env python3
"""Unit tests for dp_stage_boundary.py handoff stderr behavior."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "dp_stage_boundary.py"
POLICY = Path(__file__).resolve().parent.parent / "config" / "model_policy.yaml"


def _write_state(task_root: Path, *, last_profile: str | None = "dp-strong") -> None:
    task_root.mkdir(parents=True, exist_ok=True)
    extra = ""
    if last_profile is not None:
        extra = f'last_hermes_profile: "{last_profile}"\n'
    (task_root / "state.yaml").write_text(
        f'task_id: "20260520_boundary"\n'
        f'current_stage: "spec"\n'
        f"review_depth_preset: standard\n"
        f"{extra}",
        encoding="utf-8",
    )


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestDpStageBoundary(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.task = Path(self._tmp.name) / "task"
        _write_state(self.task)

    def test_print_markdown_row_no_handoff_on_stderr(self) -> None:
        export = self.task / "sess.jsonl"
        export.write_text(
            '{"id":"20260520_000100_a1b2c0","model":"gpt-5.5",'
            '"input_tokens":1,"output_tokens":2}\n',
            encoding="utf-8",
        )
        r = _run(
            "--task-dir",
            str(self.task),
            "--policy",
            str(POLICY),
            "--stage-id",
            "plan_review",
            "--session-export",
            str(export),
            "--print-markdown-row",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("|", r.stdout)
        self.assertNotIn("handoff_required", r.stderr)

    def test_print_json_may_emit_handoff(self) -> None:
        _write_state(self.task, last_profile="dp-code")
        r = _run(
            "--task-dir",
            str(self.task),
            "--policy",
            str(POLICY),
            "--stage-id",
            "plan_review",
            "--print-json",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("hermes_profile", data)
        if data.get("handoff_required"):
            self.assertIn("handoff_required", r.stderr)


if __name__ == "__main__":
    unittest.main()
