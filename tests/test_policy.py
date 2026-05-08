from __future__ import annotations

import unittest

from minerva_kernel import Decision, validate_action, validate_payload


class PolicyRuntimeTests(unittest.TestCase):
    def test_default_policy_allows_known_read_only_action(self) -> None:
        decision = Decision(
            failure="missing command",
            action="check_command_exists",
            confidence=0.91,
            risk="low",
            escalate=False,
            evidence=["stderr contains command not found"],
        )

        result = validate_action(decision)

        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "allowed by read-only policy")

    def test_blocks_destructive_command_attempt(self) -> None:
        result = validate_payload(
            {
                "action": "check_logs",
                "tool": None,
                "command": "rm -rf /tmp/minerva-test",
            }
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "blocked destructive command attempt")

    def test_blocks_credential_access_attempt(self) -> None:
        result = validate_payload(
            {
                "action": "inspect_file",
                "path": "~/.aws/credentials",
            }
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "blocked credential access attempt")

    def test_blocks_write_attempts_by_default(self) -> None:
        result = validate_payload(
            {
                "action": "inspect_file",
                "path": "README.md",
                "writes": True,
            }
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "blocked write attempt by read-only policy")

    def test_blocks_dangerous_action_labels(self) -> None:
        result = validate_payload(
            {
                "action": "run_command",
                "command": "pytest",
            }
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "blocked dangerous action label: run_command")

    def test_blocks_dangerous_tools(self) -> None:
        result = validate_payload(
            {
                "action": "check_logs",
                "tool": "bash",
                "command": "tail -n 20 app.log",
            }
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "blocked shell tool: bash")

    def test_blocks_unknown_actions(self) -> None:
        result = validate_payload({"action": "unknown_action"})

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "unsupported action label: unknown_action")


if __name__ == "__main__":
    unittest.main()
