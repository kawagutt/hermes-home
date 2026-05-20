#!/usr/bin/env python3
"""Unit tests for dp_review_job.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parent / "dp_review_job.py"
POLICY = Path(__file__).resolve().parent.parent / "config" / "model_policy.yaml"
TARGETS = Path(__file__).resolve().parent.parent / "config" / "review_targets.yaml"


def _write_state(task: Path, *, preset: str = "deep") -> None:
    task.mkdir(parents=True, exist_ok=True)
    (task / "state.yaml").write_text(
        f'task_id: "t1"\ncurrent_stage: "plan"\nreview_depth_preset: "{preset}"\n',
        encoding="utf-8",
    )


def _create_round(task: Path, stage: str = "plan", round_num: int = 1) -> Path:
    rdir = task / "reviews" / stage / f"round_{round_num:02d}"
    rdir.mkdir(parents=True, exist_ok=True)
    return rdir


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *cmd],
        check=False,
        capture_output=True,
        text=True,
    )


def _base_init_cmd(task: Path) -> list[str]:
    return [
        "--task-dir",
        str(task),
        "--policy",
        str(POLICY),
        "--review-targets",
        str(TARGETS),
        "--review-stage",
        "plan",
        "--round",
        "1",
    ]


class TestDpReviewJob(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.task = Path(self._tmp.name) / "task"
        _write_state(self.task, preset="deep")

    def test_print_json_reviewer(self) -> None:
        r = _run(
            _base_init_cmd(self.task) + ["--agent", "architecture", "--print-json"]
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["action"], "review_architecture")
        self.assertEqual(obj["hermes_profile"], "dp-review")
        self.assertFalse(obj["record_state"])

    def test_unknown_agent_fails(self) -> None:
        r = _run(
            _base_init_cmd(self.task) + ["--agent", "not_a_reviewer", "--print-json"]
        )
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("unknown review agent", r.stderr)

    def test_synthesis_action_uses_review_targets_yaml(self) -> None:
        custom_targets = self.task / "review_targets_custom.yaml"
        data = yaml.safe_load(TARGETS.read_text(encoding="utf-8"))
        data["presets"]["deep"]["synthesis_action"] = "review_synthesis_standard"
        custom_targets.write_text(
            yaml.dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        r = _run(
            [
                "--task-dir",
                str(self.task),
                "--policy",
                str(POLICY),
                "--review-targets",
                str(custom_targets),
                "--review-stage",
                "plan",
                "--round",
                "1",
                "--synthesis",
                "--print-json",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["action"], "review_synthesis_standard")

    def test_synthesis_action_final_stage_overrides_yaml(self) -> None:
        r = _run(
            [
                "--task-dir",
                str(self.task),
                "--policy",
                str(POLICY),
                "--review-stage",
                "final",
                "--round",
                "1",
                "--synthesis",
                "--print-json",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["action"], "review_synthesis_final")
        self.assertEqual(obj["reasoning_expected"], "high")

    def test_init_manifest_requires_round_dir(self) -> None:
        r = _run(_base_init_cmd(self.task) + ["--init-manifest"])
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("review round directory not found", r.stderr)

    def test_init_manifest_lists_required_reviewers(self) -> None:
        _create_round(self.task)
        r = _run(_base_init_cmd(self.task) + ["--init-manifest"])
        self.assertEqual(r.returncode, 0, r.stderr)
        manifest_path = self.task / "reviews/plan/round_01/review_manifest.yaml"
        self.assertTrue(manifest_path.is_file())
        text = manifest_path.read_text(encoding="utf-8")
        for agent in (
            "requirements",
            "architecture",
            "diff_detail",
            "impact",
            "test_quality",
        ):
            self.assertIn(f"{agent}:", text)
        self.assertIn("synthesis:", text)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["synthesis_action"], "review_synthesis_deep")

    def test_init_manifest_refuses_overwrite_without_force(self) -> None:
        _create_round(self.task)
        cmd = _base_init_cmd(self.task) + ["--init-manifest"]
        r1 = _run(cmd)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        (self.task / "reviews/plan/round_01/review_manifest.yaml").write_text(
            "reviewers:\n  architecture:\n    session_id: kept\n",
            encoding="utf-8",
        )
        r2 = _run(cmd)
        self.assertEqual(r2.returncode, 2, r2.stderr)
        self.assertIn("already exists", r2.stderr)

    def test_init_manifest_force_overwrites(self) -> None:
        _create_round(self.task)
        cmd = _base_init_cmd(self.task) + ["--init-manifest"]
        _run(cmd)
        r = _run(cmd + ["--force"])
        self.assertEqual(r.returncode, 0, r.stderr)
        text = (self.task / "reviews/plan/round_01/review_manifest.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("review_stage:", text)
        self.assertNotIn("session_id: kept", text)

    def test_record_session_updates_manifest(self) -> None:
        _create_round(self.task)
        _run(_base_init_cmd(self.task) + ["--init-manifest"])
        export = self.task / "session.jsonl"
        export.write_text(
            json.dumps(
                {
                    "id": "20260520_test_sess",
                    "model": "gpt-5.5",
                    "input_tokens": 100,
                    "output_tokens": 10,
                    "reasoning_tokens": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        r = _run(
            [
                "--task-dir",
                str(self.task),
                "--review-stage",
                "plan",
                "--round",
                "1",
                "--agent",
                "architecture",
                "--record-session",
                "--session-export",
                str(export),
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        manifest = (self.task / "reviews/plan/round_01/review_manifest.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("20260520_test_sess", manifest)
        self.assertIn("usage_evidence:", manifest)


if __name__ == "__main__":
    unittest.main()
