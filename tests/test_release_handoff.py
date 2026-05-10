from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release-handoff.py"


def load_handoff():
    spec = importlib.util.spec_from_file_location("release_handoff", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load release handoff")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handoff = load_handoff()

    def test_clean_handoff_is_ready_when_dashboard_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=0)

            payload = self.handoff.build_handoff(
                root=root,
                runner=_runner(git_status=""),
                timeout_seconds=5,
            )

        self.assertEqual(payload["schema_version"], "minerva.release_handoff.v0")
        self.assertTrue(payload["ready_for_release_review"])
        self.assertTrue(payload["git_status"]["clean"])
        self.assertEqual(payload["changed_file_inventory"]["total"], 0)
        self.assertEqual(payload["blockers"], [])

    def test_dirty_worktree_is_categorized_and_blocks_handoff(self) -> None:
        status = "\n".join(
            [
                " M README.md",
                " M minerva_kernel/daemon.py",
                "?? tests/test_release_handoff.py",
                "?? .tasks/T59.task.md",
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=0)

            payload = self.handoff.build_handoff(
                root=root,
                runner=_runner(git_status=status),
                timeout_seconds=5,
            )

        self.assertFalse(payload["ready_for_release_review"])
        self.assertEqual(payload["git_status"]["changed_file_count"], 4)
        categories = payload["changed_file_inventory"]["categories"]
        self.assertEqual(categories["docs"]["count"], 1)
        self.assertEqual(categories["kernel"]["count"], 1)
        self.assertEqual(categories["tests"]["count"], 1)
        self.assertEqual(categories["task_queue"]["count"], 1)
        self.assertIn("dirty_worktree", {blocker["name"] for blocker in payload["blockers"]})

    def test_dashboard_failure_is_reported_as_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=1)

            payload = self.handoff.build_handoff(
                root=root,
                runner=_runner(git_status=""),
                timeout_seconds=5,
            )

        self.assertFalse(payload["ready_for_release_review"])
        blockers = {(item["source"], item["name"]) for item in payload["blockers"]}
        self.assertIn(("release_ops_dashboard", "task_queue"), blockers)

    def test_git_status_failure_is_reported_without_file_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _root_with_board(Path(tmpdir), pending=0)

            payload = self.handoff.build_handoff(
                root=root,
                runner=_runner(git_status_error=True),
                timeout_seconds=5,
            )

        self.assertFalse(payload["ready_for_release_review"])
        self.assertEqual(payload["git_status"]["exit_code"], 2)
        self.assertEqual(payload["changed_file_inventory"]["total"], 0)
        blockers = {(item["source"], item["name"]) for item in payload["blockers"]}
        self.assertIn(("git_status", "git_status_failed"), blockers)


def _runner(*, git_status: str = "", git_status_error: bool = False):
    handoff = load_handoff()

    def run(command: Sequence[str], timeout_seconds: int):
        command_list = list(command)
        if command_list == ["git", "status", "--porcelain"]:
            if git_status_error:
                return handoff.CommandResult(2, "", "not a git repository\n")
            return handoff.CommandResult(0, git_status, "")
        if "minerva_kernel.cpu_model_eval" in command:
            return handoff.CommandResult(
                0,
                json.dumps({"decision": "promote", "corpus": {"case_count": 30}}),
                "",
            )
        return handoff.CommandResult(0, "ok\n", "")

    return run


def _root_with_board(root: Path, *, pending: int) -> Path:
    tasks = root / ".tasks"
    tasks.mkdir()
    lines = [
        "| ID | GitHub | Status | Owner Lane | Title |",
        "|---|---|---|---|---|",
        "| T1 | #1 | done | Kernel | Done |",
    ]
    for index in range(pending):
        lines.append(f"| T{index + 2} | #{index + 2} | pending | Release | Pending |")
    (tasks / "board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


if __name__ == "__main__":
    unittest.main()
