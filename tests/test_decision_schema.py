from __future__ import annotations

import unittest

from minerva_kernel import Decision, INSTRUCTION_SET_V0


class DecisionSchemaTests(unittest.TestCase):
    def test_decision_minimal_example(self) -> None:
        decision = Decision(
            failure="module import failed",
            action="inspect_dependencies",
            confidence=0.82,
            risk="low",
            escalate=False,
            evidence=["stderr contains ModuleNotFoundError"],
        )

        self.assertEqual(
            decision.to_dict(),
            {
                "schema_version": "decision.v0",
                "failure": "module import failed",
                "action": "inspect_dependencies",
                "confidence": 0.82,
                "risk": "low",
                "escalate": False,
                "evidence": ["stderr contains ModuleNotFoundError"],
            },
        )

    def test_decision_includes_optional_reason(self) -> None:
        decision = Decision(
            failure="network unavailable",
            action="ask_user",
            confidence=0.64,
            risk="medium",
            escalate=True,
            evidence=["network_status is unknown"],
            reason="Need user confirmation before checking external network.",
        )

        self.assertEqual(
            decision.to_dict()["reason"],
            "Need user confirmation before checking external network.",
        )

    def test_instruction_set_v0_accepts_all_labels(self) -> None:
        expected = {
            "stop",
            "retry",
            "check_dns",
            "check_network",
            "check_port",
            "inspect_file",
            "inspect_dependencies",
            "search_local",
            "check_command_exists",
            "check_permissions",
            "check_service_status",
            "check_logs",
            "ask_bigger_llm",
            "ask_user",
        }

        self.assertEqual(set(INSTRUCTION_SET_V0), expected)
        for action in INSTRUCTION_SET_V0:
            decision = Decision(
                failure="test failure",
                action=action,
                confidence=0.9,
                risk="low",
                escalate=False,
                evidence=["test evidence"],
            )
            self.assertEqual(decision.action, action)

    def test_decision_rejects_unsupported_action_labels(self) -> None:
        for action in ("run_command", "run_safe_command", "shell", "repair"):
            with self.subTest(action=action):
                with self.assertRaisesRegex(ValueError, "unsupported action"):
                    Decision.from_dict(
                        {
                            "failure": "test failure",
                            "action": action,
                            "confidence": 0.9,
                            "risk": "low",
                            "escalate": False,
                            "evidence": ["test evidence"],
                        }
                    )

    def test_decision_rejects_invalid_confidence_and_empty_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "confidence"):
            Decision(
                failure="test failure",
                action="retry",
                confidence=1.1,
                risk="low",
                escalate=False,
                evidence=["test evidence"],
            )

        with self.assertRaisesRegex(ValueError, "evidence"):
            Decision(
                failure="test failure",
                action="retry",
                confidence=0.9,
                risk="low",
                escalate=False,
                evidence=[],
            )

    def test_decision_rejects_non_boolean_escalate(self) -> None:
        with self.assertRaisesRegex(ValueError, "escalate"):
            Decision.from_dict(
                {
                    "failure": "test failure",
                    "action": "retry",
                    "confidence": 0.9,
                    "risk": "low",
                    "escalate": "false",
                    "evidence": ["test evidence"],
                }
            )


if __name__ == "__main__":
    unittest.main()
