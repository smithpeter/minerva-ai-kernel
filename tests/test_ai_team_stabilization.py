from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-ai-team-stabilization.py"
DOC = ROOT / "docs" / "ai-team-stabilization.md"


def load_stabilization():
    spec = importlib.util.spec_from_file_location("check_ai_team_stabilization", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load stabilization check")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AiTeamStabilizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.check = load_stabilization()

    def test_current_repo_has_stabilization_docs_and_check(self) -> None:
        text = DOC.read_text(encoding="utf-8")

        self.assertIn("scope expansion", text)
        self.assertIn("release handoff", text)
        self.assertIn("scripts/check-ai-team-stabilization.py", text)

    def test_status_ready_when_no_pending_and_required_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _fake_root(Path(tmpdir), pending=0)

            payload = self.check.stabilization_status(root)

        self.assertTrue(payload["ready"])
        self.assertEqual(payload["pending_count"], 0)
        self.assertEqual(payload["missing_required_files"], [])
        self.assertEqual(payload["next_phase"], "release_handoff")

    def test_status_blocks_pending_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _fake_root(Path(tmpdir), pending=2)

            payload = self.check.stabilization_status(root)

        self.assertFalse(payload["ready"])
        self.assertEqual(payload["pending_count"], 2)
        self.assertEqual(payload["next_phase"], "finish_pending_tasks")

    def test_status_blocks_missing_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _fake_root(Path(tmpdir), pending=0)
            (root / "scripts" / "release-handoff.py").unlink()

            payload = self.check.stabilization_status(root)

        self.assertFalse(payload["ready"])
        self.assertIn("scripts/release-handoff.py", payload["missing_required_files"])


def _fake_root(root: Path, *, pending: int) -> Path:
    (root / ".tasks").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "scripts").mkdir()
    for path in (
        "docs/plan-eng-review-workflow.md",
        "docs/ai-team-task-template.md",
        "docs/ai-team-stabilization.md",
        "scripts/check-plan-eng-review.sh",
        "scripts/release-ops-dashboard.py",
        "scripts/release-handoff.py",
    ):
        target = root / path
        target.write_text("placeholder\n", encoding="utf-8")
    lines = [
        "| ID | GitHub | Status | Owner Lane | Title |",
        "|---|---|---|---|---|",
        "| T1 | #1 | done | Kernel | Done |",
    ]
    for index in range(pending):
        lines.append(f"| T{index + 2} | #{index + 2} | pending | Ops | Pending |")
    (root / ".tasks" / "board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


if __name__ == "__main__":
    unittest.main()
