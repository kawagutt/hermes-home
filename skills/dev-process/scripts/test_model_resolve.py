#!/usr/bin/env python3
"""Unit tests for model_resolve.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from model_resolve import (
    ModelResolveError,
    load_task_state,
    resolve_for_task,
    resolve_model,
    validate_policy,
)
from model_resolve import load_yaml, default_policy_path


POLICY = default_policy_path()


class TestModelResolve(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)
        self.policy = validate_policy(load_yaml(POLICY))

    def _write_state(self, task_id: str, **fields: object) -> Path:
        task = self.tmp_path / task_id
        task.mkdir(parents=True, exist_ok=True)
        lines = [f'task_id: "{task_id}"', 'current_stage: "implementation"']
        for key, val in fields.items():
            if isinstance(val, str):
                lines.append(f'{key}: "{val}"')
            elif isinstance(val, bool):
                lines.append(f"{key}: {'true' if val else 'false'}")
            else:
                lines.append(f"{key}: {val}")
        (task / "state.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return task

    def test_schema_version_2_only(self) -> None:
        bad = dict(self.policy)
        bad["schema_version"] = 1
        with self.assertRaises(ModelResolveError):
            validate_policy(bad)

    def test_stage_id_spec_review_dp_strong(self) -> None:
        task = self._write_state("t1", review_depth_preset="deep")
        r = resolve_for_task(task, stage_id="spec_review")
        self.assertEqual(r["hermes_profile"], "dp-strong")
        self.assertEqual(r["action"], "spec")
        self.assertEqual(r["reasoning_expected"], "high")
        self.assertEqual(r["reasoning_source"], "policy_expected")

    def test_stage_id_implementation_review_dp_review(self) -> None:
        task = self._write_state("t3", review_depth_preset="deep")
        r = resolve_for_task(task, stage_id="implementation_review")
        self.assertEqual(r["role"], "review_main")
        self.assertEqual(r["hermes_profile"], "dp-review")
        self.assertEqual(r["action"], "review_standard")
        self.assertEqual(r["reasoning_expected"], "medium")

    def test_action_review_architecture_dp_review(self) -> None:
        task = self._write_state("t_rev", review_depth_preset="deep")
        r = resolve_for_task(task, action="review_architecture")
        self.assertEqual(r["hermes_profile"], "dp-review")
        self.assertEqual(r["role"], "review_main")
        self.assertEqual(r["action"], "review_architecture")

    def test_action_review_synthesis_deep_dp_strong(self) -> None:
        task = self._write_state("t_syn", review_depth_preset="deep")
        r = resolve_for_task(task, action="review_synthesis_deep")
        self.assertEqual(r["hermes_profile"], "dp-strong")
        self.assertEqual(r["reasoning_expected"], "high")

    def test_action_review_synthesis_final_dp_strong_high(self) -> None:
        task = self._write_state("t_syn_f", review_depth_preset="standard")
        r = resolve_for_task(task, action="review_synthesis_final")
        self.assertEqual(r["hermes_profile"], "dp-strong")
        self.assertEqual(r["reasoning_expected"], "high")

    def test_stage_id_implementation_dp_code(self) -> None:
        task = self._write_state("t_impl")
        r = resolve_for_task(task, stage_id="implementation")
        self.assertEqual(r["hermes_profile"], "dp-code")
        self.assertEqual(r["action"], "implement")
        self.assertEqual(r["role"], "code_main")
        self.assertEqual(r["reasoning_expected"], "medium")

    def test_implementation_final_not_a_usage_stage_id(self) -> None:
        task = self._write_state("t_impl_bad")
        with self.assertRaises(ModelResolveError) as ctx:
            resolve_for_task(task, stage_id="implementation-final")
        self.assertIn("expected stage_actions key", str(ctx.exception))

    def test_handoff_required_when_profile_changes(self) -> None:
        task = self._write_state("t4", last_hermes_profile="dp-strong")
        r = resolve_for_task(task, stage_id="test_review")
        self.assertEqual(r["hermes_profile"], "dp-code")
        self.assertTrue(r["handoff_required"])

    def test_context_reset_recommended_same_profile_review(self) -> None:
        task = self._write_state("t_ctx", last_hermes_profile="dp-strong")
        r = resolve_for_task(task, stage_id="spec_review")
        self.assertFalse(r["handoff_required"])
        self.assertTrue(r["context_reset_recommended"])

    def test_no_handoff_when_last_profile_missing(self) -> None:
        task = self._write_state("t4b", review_depth_preset="deep")
        r = resolve_for_task(task, stage_id="spec_review")
        self.assertFalse(r["handoff_required"])
        self.assertTrue(r["last_profile_unknown"])

    def test_preset_inferred_from_plan_when_state_empty(self) -> None:
        task = self._write_state("t7b", review_depth_preset="")
        (task / "0001_plan.md").write_text(
            "| **Selected review-depth preset** | `deep` |\n", encoding="utf-8"
        )
        state = load_task_state(task)
        state["artifacts"] = {"plan": "0001_plan.md"}
        r = resolve_model(
            self.policy,
            state=state,
            task_dir=task,
            stage_id="spec_review",
        )
        self.assertEqual(r["review_depth_preset"], "deep")
        self.assertNotIn("reasoning_note", r)

    def test_unknown_stage_id_raises(self) -> None:
        task = self._write_state("t6")
        with self.assertRaises(ModelResolveError):
            resolve_for_task(task, stage_id="not_a_stage")

    def test_unknown_current_stage_raises(self) -> None:
        task = self._write_state("t6b")
        state = load_task_state(task)
        state["current_stage"] = "spec_review"
        with self.assertRaises(ModelResolveError):
            resolve_model(self.policy, state=state, task_dir=task)


if __name__ == "__main__":
    unittest.main()
