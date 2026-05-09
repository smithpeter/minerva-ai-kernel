from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from minerva_kernel import Decision, Observation, execute_action


class ExecutorTests(unittest.TestCase):
    def test_blocks_policy_denied_action_before_inspection(self) -> None:
        result = execute_action(
            Decision(
                failure="needs escalation",
                action="ask_user",
                confidence=0.95,
                risk="low",
                escalate=True,
                evidence=["operator needed"],
            ),
            cwd="/tmp",
        )

        self.assertEqual(result.source, "kernel_executor")
        self.assertIn("policy blocked executor action", result.stderr_tail)
        self.assertEqual(result.runtime["policy_allowed"], False)

    def test_check_command_exists_uses_observation_without_shell(self) -> None:
        observation = _observation(command=f"{sys.executable} -m unittest")
        decision = _decision("check_command_exists")

        result = execute_action(decision, cwd="/tmp", observation=observation)

        self.assertEqual(result.command, "executor:check_command_exists")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("command found", result.stdout_tail)
        self.assertEqual(result.runtime["checked_command"], Path(sys.executable).name)
        self.assertEqual(result.runtime["found"], True)

    def test_check_command_exists_extracts_missing_command_from_stderr(self) -> None:
        observation = _observation(
            command="agent_tool:local_search",
            stderr_tail="ToolCallError: command not found: minerva-missing-tool",
        )

        result = execute_action(
            _decision("check_command_exists"),
            cwd="/tmp",
            observation=observation,
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("command not found on PATH: minerva-missing-tool", result.stdout_tail)
        self.assertEqual(result.runtime["checked_command"], "minerva-missing-tool")

    def test_inspect_dependencies_reports_local_metadata_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject = Path(tmpdir, "pyproject.toml")
            pyproject.write_text("[project]\n", encoding="utf-8")
            before = _tree_snapshot(tmpdir)

            result = execute_action(_decision("inspect_dependencies"), cwd=tmpdir)

            after = _tree_snapshot(tmpdir)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("pyproject.toml", result.stdout_tail)
        self.assertEqual(result.runtime["executor_state"], "completed")
        self.assertEqual(before, after)

    def test_check_permissions_reports_cwd_and_command_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "script.sh"
            script.write_text("#!/bin/sh\n", encoding="utf-8")
            observation = _observation(command=f"sh {script.name}")

            result = execute_action(
                _decision("check_permissions"),
                cwd=tmpdir,
                observation=observation,
            )

        self.assertIn("exists=True", result.stdout_tail)
        self.assertIn("readable=True", result.stdout_tail)
        self.assertEqual(result.runtime["executor_state"], "completed")

    def test_check_permissions_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            observation = _observation(command="cat ../outside.txt")

            result = execute_action(
                _decision("check_permissions"),
                cwd=tmpdir,
                observation=observation,
            )

        self.assertEqual(result.runtime["executor_state"], "path_rejected")
        self.assertIn("rejected unsafe path candidate", result.stderr_tail)

    def test_check_permissions_rejects_credential_like_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            observation = _observation(command="cat .env")

            result = execute_action(
                _decision("check_permissions"),
                cwd=tmpdir,
                observation=observation,
            )

        self.assertEqual(result.runtime["executor_state"], "path_rejected")
        self.assertIn(".env", result.stderr_tail)

    def test_check_logs_summarizes_existing_observation_tails(self) -> None:
        observation = _observation(stderr_tail="Traceback: boom")

        result = execute_action(_decision("check_logs"), cwd="/tmp", observation=observation)

        self.assertIn("stderr_tail_chars=", result.stdout_tail)
        self.assertIn("Traceback: boom", result.stdout_tail)
        self.assertEqual(result.runtime["executor_state"], "completed")


def _decision(action: str) -> Decision:
    return Decision(
        failure="test_failure",
        action=action,  # type: ignore[arg-type]
        confidence=0.91,
        risk="low",
        escalate=False,
        evidence=["test evidence"],
    )


def _observation(
    *,
    command: str = "python -m unittest",
    stderr_tail: str = "",
) -> Observation:
    return Observation(
        command=command,
        cwd="/workspace/example",
        exit_code=1,
        stdout_tail="",
        stderr_tail=stderr_tail,
        duration_ms=10,
        source="executor_test",
        policy_summary="bounded executor test observation",
    )


def _tree_snapshot(root: str) -> dict[str, str]:
    base = Path(root)
    return {
        str(path.relative_to(base)): path.read_text(encoding="utf-8")
        for path in sorted(base.rglob("*"))
        if path.is_file()
    }


if __name__ == "__main__":
    unittest.main()
