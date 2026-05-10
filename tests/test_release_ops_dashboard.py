from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release-ops-dashboard.py"


def load_dashboard():
    spec = importlib.util.spec_from_file_location("release_ops_dashboard", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load release ops dashboard")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseOpsDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dashboard = load_dashboard()

    def test_collect_status_reports_ready_when_all_local_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=0)
            calls: list[list[str]] = []

            payload = self.dashboard.collect_status(
                root=root,
                runner=_passing_runner(calls),
                timeout_seconds=5,
            )

        self.assertEqual(payload["schema_version"], "release_ops_status.v0")
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["summary"]["fail"], 0)
        self.assertIn("release_readiness_local", _check_names(payload))
        release_command = _check(payload, "release_readiness_local")["command"]
        self.assertIn("--skip-external", release_command)
        self.assertIn(["git", "status", "--porcelain"], calls)

    def test_collect_status_surfaces_failed_subcheck(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=0)

            payload = self.dashboard.collect_status(
                root=root,
                runner=_failing_runner("scripts/check-plan-eng-review.sh"),
                timeout_seconds=5,
            )

        self.assertFalse(payload["ready"])
        plan_eng = _check(payload, "plan_eng_review")
        self.assertEqual(plan_eng["status"], "fail")
        self.assertEqual(plan_eng["exit_code"], 1)

    def test_pending_tasks_block_release_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=2)

            payload = self.dashboard.collect_status(
                root=root,
                runner=_passing_runner([]),
                timeout_seconds=5,
            )

        self.assertFalse(payload["ready"])
        task_queue = _check(payload, "task_queue")
        self.assertEqual(task_queue["status"], "fail")
        self.assertEqual(task_queue["summary"], "done=2 pending=2")

    def test_dirty_worktree_blocks_release_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=0)

            payload = self.dashboard.collect_status(
                root=root,
                runner=_dirty_runner,
                timeout_seconds=5,
            )

        self.assertFalse(payload["ready"])
        worktree = _check(payload, "worktree")
        self.assertEqual(worktree["status"], "fail")
        self.assertIn("dirty worktree", worktree["summary"])

    def test_cpu_eval_must_return_promote_json(self) -> None:
        payload = self.dashboard.check_cpu_eval(
            runner=_cpu_reject_runner,
            timeout_seconds=5,
        )

        self.assertEqual(payload.status, "fail")
        self.assertEqual(payload.summary, "cpu eval decision=reject")


def _passing_runner(calls: list[list[str]]):
    dashboard = load_dashboard()

    def run(command: Sequence[str], timeout_seconds: int):
        calls.append(list(command))
        if list(command) == ["git", "status", "--porcelain"]:
            return dashboard.CommandResult(0, "", "")
        if "minerva_kernel.cpu_model_eval" in command:
            return dashboard.CommandResult(
                0,
                json.dumps({"decision": "promote", "corpus": {"case_count": 30}}),
                "",
            )
        return dashboard.CommandResult(0, "ok\n", "")

    return run


def _failing_runner(command_fragment: str):
    dashboard = load_dashboard()

    def run(command: Sequence[str], timeout_seconds: int):
        if any(command_fragment in part for part in command):
            return dashboard.CommandResult(1, "", "failed\n")
        if list(command) == ["git", "status", "--porcelain"]:
            return dashboard.CommandResult(0, "", "")
        if "minerva_kernel.cpu_model_eval" in command:
            return dashboard.CommandResult(
                0,
                json.dumps({"decision": "promote", "corpus": {"case_count": 30}}),
                "",
            )
        return dashboard.CommandResult(0, "ok\n", "")

    return run


def _dirty_runner(command: Sequence[str], timeout_seconds: int):
    dashboard = load_dashboard()
    if list(command) == ["git", "status", "--porcelain"]:
        return dashboard.CommandResult(0, " M README.md\n", "")
    if "minerva_kernel.cpu_model_eval" in command:
        return dashboard.CommandResult(
            0,
            json.dumps({"decision": "promote", "corpus": {"case_count": 30}}),
            "",
        )
    return dashboard.CommandResult(0, "ok\n", "")


def _cpu_reject_runner(command: Sequence[str], timeout_seconds: int):
    dashboard = load_dashboard()
    return dashboard.CommandResult(0, json.dumps({"decision": "reject"}), "")


def _root_with_board(root: Path, *, pending: int) -> Path:
    tasks = root / ".tasks"
    tasks.mkdir()
    lines = [
        "| ID | GitHub | Status | Owner Lane | Title |",
        "|---|---|---|---|---|",
        "| T1 | #1 | done | Kernel | Done one |",
        "| T2 | #2 | done | Kernel | Done two |",
    ]
    for index in range(pending):
        lines.append(f"| T{index + 3} | #{index + 3} | pending | Release | Pending |")
    (tasks / "board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def _check_names(payload: dict[str, object]) -> set[str]:
    return {str(check["name"]) for check in payload["checks"]}  # type: ignore[index]


def _check(payload: dict[str, object], name: str) -> dict[str, object]:
    for check in payload["checks"]:  # type: ignore[index]
        if check["name"] == name:
            return check
    raise AssertionError(f"missing check: {name}")


if __name__ == "__main__":
    unittest.main()
