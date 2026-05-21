#!/usr/bin/env python3
"""Unit tests for dp_hermes.py (no Hermes subprocess; uses --print-profile-only / --print-json only)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "dp_hermes.py"
POLICY = Path(__file__).resolve().parent.parent / "config" / "model_policy.yaml"


def _write_state(
    task_root: Path,
    task_id: str,
    current_stage: str,
    *,
    last_hermes_profile: str | None = None,
) -> None:
    task_root.mkdir(parents=True, exist_ok=True)
    extra = ""
    if last_hermes_profile is not None:
        extra = f'last_hermes_profile: "{last_hermes_profile}"\n'
    (task_root / "state.yaml").write_text(
        f'task_id: "{task_id}"\ncurrent_stage: "{current_stage}"\n{extra}',
        encoding="utf-8",
    )


def _run(
    *,
    task_dir: Path,
    action: str | None = None,
    stage_id: str | None = None,
    print_profile_only: bool = False,
    print_json: bool = False,
    handoff_only: bool = False,
    record_state: bool = False,
    hermes_args: list[str] | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd: list[str] = [
        sys.executable,
        str(SCRIPT),
        "--task-dir",
        str(task_dir),
        "--policy",
        str(POLICY),
    ]
    if action is not None:
        cmd.extend(["--action", action])
    if stage_id is not None:
        cmd.extend(["--stage-id", stage_id])
    if print_profile_only:
        cmd.append("--print-profile-only")
    if print_json:
        cmd.append("--print-json")
    if handoff_only:
        cmd.append("--handoff-only")
    if record_state:
        cmd.append("--record-state")
    if hermes_args:
        cmd.append("--")
        cmd.extend(hermes_args)
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


class TestDpHermesResolve(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def test_action_write_tests_dp_code(self) -> None:
        task = self.tmp_path / "t1"
        _write_state(task, "t1", "implementation")
        r = _run(task_dir=task, action="write_tests", print_profile_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "dp-code")
        self.assertEqual(r.stderr.strip(), "")

    def test_action_run_tests_dp_cheap(self) -> None:
        task = self.tmp_path / "t2"
        _write_state(task, "t2", "implementation")
        r = _run(task_dir=task, action="run_tests", print_profile_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "dp-cheap")

    def test_action_final_review_dp_strong(self) -> None:
        task = self.tmp_path / "t3"
        _write_state(task, "t3", "implementation")
        r = _run(task_dir=task, action="final_review", print_profile_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "dp-strong")

    def test_action_spec_dp_strong(self) -> None:
        task = self.tmp_path / "t_spec"
        _write_state(task, "t_spec", "implementation")
        r = _run(task_dir=task, action="spec", print_profile_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "dp-strong")

    def test_action_plan_dp_strong(self) -> None:
        task = self.tmp_path / "t_plan"
        _write_state(task, "t_plan", "implementation")
        r = _run(task_dir=task, action="plan", print_profile_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "dp-strong")

    def test_unknown_action_exit_2(self) -> None:
        task = self.tmp_path / "t4"
        _write_state(task, "t4", "implementation")
        r = _run(task_dir=task, action="bad_action", print_profile_only=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown action", r.stderr)

    def test_unknown_stage_exit_2(self) -> None:
        task = self.tmp_path / "t6"
        _write_state(task, "t6", "not_a_real_stage")
        r = _run(task_dir=task, action=None, print_profile_only=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown current_stage", r.stderr)

    def test_stage_id_spec_review_dp_strong(self) -> None:
        task = self.tmp_path / "t_stage"
        _write_state(task, "t_stage", "spec")
        r = _run(task_dir=task, stage_id="spec_review", print_profile_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "dp-strong")

    def test_stage_id_human_spec_gate_dp_cheap(self) -> None:
        task = self.tmp_path / "t_gate"
        _write_state(task, "t_gate", "spec")
        r = _run(task_dir=task, stage_id="human_spec_gate", print_profile_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "dp-cheap")

    def test_print_profile_only_stdout_is_profile_name_only(self) -> None:
        task = self.tmp_path / "t7"
        _write_state(task, "t7", "implementation")
        r = _run(task_dir=task, action="write_tests", print_profile_only=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "dp-code\n")
        self.assertNotIn("\n\n", r.stdout)

    def test_print_json_valid_json_only(self) -> None:
        task = self.tmp_path / "t8"
        _write_state(task, "t8", "implementation")
        r = _run(task_dir=task, action="write_tests", print_json=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["hermes_profile"], "dp-code")
        self.assertEqual(obj["resolution_source"], "action")
        self.assertEqual(r.stderr.strip(), "")

    def test_print_json_stage_resolution(self) -> None:
        task = self.tmp_path / "t9"
        _write_state(task, "t9", "test")
        r = _run(task_dir=task, print_json=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["resolution_source"], "stage")
        self.assertEqual(obj["hermes_profile"], "dp-code")
        self.assertIsNone(obj["action"])

    def test_handoff_only_prints_json_without_hermes(self) -> None:
        task = self.tmp_path / "t_handoff"
        _write_state(
            task,
            "t_handoff",
            "implementation",
            last_hermes_profile="dp-strong",
        )
        r = _run(task_dir=task, stage_id="test_review", handoff_only=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertTrue(obj["handoff_required"])
        self.assertEqual(obj["hermes_profile"], "dp-code")
        self.assertIn("handoff_required", r.stderr)
        self.assertNotIn("Model usage:", r.stdout)

    def test_probe_failure_exit_2_when_hermes_missing(self) -> None:
        task = self.tmp_path / "t10"
        _write_state(task, "t10", "implementation")
        r = _run(
            task_dir=task,
            action="write_tests",
            hermes_args=["version"],
            env_overrides={"HERMES_EXE": "/no/such/hermes"},
        )
        self.assertEqual(r.returncode, 2)
        self.assertIn("failed to run Hermes executable", r.stderr)

    def test_record_state_updates_only_on_success(self) -> None:
        task = self.tmp_path / "t11"
        _write_state(task, "t11", "implementation")
        fake_hermes = self.tmp_path / "fake_hermes_ok.sh"
        fake_hermes.write_text(
            "#!/usr/bin/env bash\n"
            'if [ "$2" = "version" ]; then exit 0; fi\n'
            "exit 0\n",
            encoding="utf-8",
        )
        fake_hermes.chmod(0o755)

        r = _run(
            task_dir=task,
            action="write_tests",
            record_state=True,
            hermes_args=["version"],
            env_overrides={"HERMES_EXE": str(fake_hermes)},
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        state = (task / "state.yaml").read_text(encoding="utf-8")
        self.assertIn("last_hermes_profile: dp-code", state)
        self.assertIn("last_dev_process_action: write_tests", state)
        self.assertIn("last_resolution_source: action", state)

    def test_implementation_without_stage_id_exits_2_by_default(self) -> None:
        task = self.tmp_path / "t_impl_strict"
        _write_state(task, "t_impl_strict", "implementation")
        r = _run(task_dir=task, print_json=True)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("current_stage=implementation", r.stderr)
        self.assertNotIn("WARNING:", r.stderr)

    def test_review_worker_action_rejects_record_state(self) -> None:
        task = self.tmp_path / "t_rev_guard"
        _write_state(task, "t_rev_guard", "plan")
        r = _run(
            task_dir=task,
            action="review_architecture",
            record_state=True,
            print_json=True,
        )
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("review worker", r.stderr.lower())

    def test_final_review_action_allows_record_state_flag(self) -> None:
        task = self.tmp_path / "t_final_rev"
        _write_state(task, "t_final_rev", "final", last_hermes_profile="dp-code")
        r = _run(
            task_dir=task,
            action="final_review",
            record_state=True,
            print_json=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["action"], "final_review")
        self.assertEqual(obj["hermes_profile"], "dp-strong")

    def test_record_state_not_updated_on_failure(self) -> None:
        task = self.tmp_path / "t12"
        _write_state(task, "t12", "implementation")
        original = (task / "state.yaml").read_text(encoding="utf-8")
        fake_hermes = self.tmp_path / "fake_hermes_fail.sh"
        fake_hermes.write_text(
            "#!/usr/bin/env bash\n"
            'if [ "$2" = "version" ]; then exit 0; fi\n'
            "exit 7\n",
            encoding="utf-8",
        )
        fake_hermes.chmod(0o755)

        r = _run(
            task_dir=task,
            action="write_tests",
            record_state=True,
            hermes_args=["chat", "-q", "hello"],
            env_overrides={"HERMES_EXE": str(fake_hermes)},
        )
        self.assertEqual(r.returncode, 7, r.stderr)
        after = (task / "state.yaml").read_text(encoding="utf-8")
        self.assertEqual(after, original)


def _load_dp_hermes_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("dp_hermes_under_test", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestValidatePolicyInline(unittest.TestCase):
    """Bundled model_policy.yaml passes startup validation (role / profile consistency)."""

    def test_bundled_policy_loads(self) -> None:
        mod = _load_dp_hermes_module()
        data = mod._load_yaml(POLICY)
        mod._validate_policy(data)


if __name__ == "__main__":
    unittest.main()
