#!/usr/bin/env python3
"""Unit tests for session_usage.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "session_usage.py"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


class TestSessionUsage(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def _write(self, name: str, content: str) -> Path:
        p = self.tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_valid_single_line_json_output(self) -> None:
        p = self._write(
            "ok.jsonl",
            '{"id":"s1","model":"gpt-5.5","input_tokens":1200,"output_tokens":300,"reasoning_tokens":50}\n',
        )
        r = _run([str(p), "--format", "json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["session_id"], "s1")
        self.assertEqual(obj["model"], "gpt-5.5")

    def test_valid_single_line_markdown_compact_columns(self) -> None:
        p = self._write(
            "ok_md.jsonl",
            '{"id":"s2","model":"gpt-5.5","input_tokens":10,"output_tokens":2,"reasoning_tokens":1,"started_at":0,"ended_at":10}\n',
        )
        r = _run(
            [
                str(p),
                "--format",
                "markdown",
                "--stage-id",
                "test_review",
                "--time",
                "auto",
                "--action",
                "write_tests",
                "--role",
                "code_main",
                "--profile",
                "dp-code",
                "--preset",
                "deep",
                "--reasoning",
                "expected medium / observed unknown",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| `test_review` | write_tests | dp-code / code_main |", r.stdout)
        self.assertIn("| deep / expected medium / observed unknown |", r.stdout)
        self.assertIn("in=10, out=2", r.stdout)

    def test_empty_file_exit_2(self) -> None:
        p = self._write("empty.jsonl", "")
        r = _run([str(p), "--format", "json"])
        self.assertEqual(r.returncode, 2)

    def test_markdown_escapes_pipe_in_cells(self) -> None:
        p = self._write(
            "escape.jsonl",
            '{"id":"s6","model":"gpt|5.5","input_tokens":1,"output_tokens":1,"reasoning_tokens":0}\n',
        )
        r = _run([str(p), "--format", "markdown", "--evidence", "foo|bar"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(r"gpt\|5.5", r.stdout)


if __name__ == "__main__":
    unittest.main()
