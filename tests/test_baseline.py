from __future__ import annotations

import unittest

from minerva_kernel import Decision, MockModelProvider, Observation, diagnose_observation


class BaselineInterpreterTests(unittest.TestCase):
    def test_default_diagnosis_handles_missing_dependency_without_provider(self) -> None:
        diagnosis = diagnose_observation(
            _observation(stderr_tail="ModuleNotFoundError: No module named 'yaml'")
        )

        self.assertEqual(diagnosis.decision.failure, "missing_dependency")
        self.assertEqual(diagnosis.decision.action, "inspect_dependencies")
        self.assertFalse(diagnosis.decision.escalate)
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_handles_command_not_found(self) -> None:
        diagnosis = diagnose_observation(
            _observation(
                exit_code=127,
                stderr_tail="command not found: minerva-missing",
                runtime={"command_found": False},
            )
        )

        self.assertEqual(diagnosis.decision.failure, "command_not_found")
        self.assertEqual(diagnosis.decision.action, "check_command_exists")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_handles_timeout(self) -> None:
        diagnosis = diagnose_observation(
            _observation(
                exit_code=124,
                stderr_tail="Command timed out after 1 seconds",
                runtime={"timed_out": True},
            )
        )

        self.assertEqual(diagnosis.decision.failure, "command_timeout")
        self.assertEqual(diagnosis.decision.action, "check_logs")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_handles_permission_denied(self) -> None:
        diagnosis = diagnose_observation(
            _observation(exit_code=126, stderr_tail="permission denied: ./script.sh")
        )

        self.assertEqual(diagnosis.decision.failure, "permission_denied")
        self.assertEqual(diagnosis.decision.action, "check_permissions")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_handles_npm_script_failure(self) -> None:
        diagnosis = diagnose_observation(
            _observation(stderr_tail="npm ERR! Missing script: test")
        )

        self.assertEqual(
            diagnosis.decision.failure,
            "node_package_or_script_failure",
        )
        self.assertEqual(diagnosis.decision.action, "inspect_dependencies")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_handles_git_repository_failure(self) -> None:
        diagnosis = diagnose_observation(
            _observation(stderr_tail="fatal: not a git repository")
        )

        self.assertEqual(diagnosis.decision.failure, "git_repository_failure")
        self.assertEqual(diagnosis.decision.action, "check_logs")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_handles_container_build_failure(self) -> None:
        diagnosis = diagnose_observation(
            _observation(stderr_tail="Dockerfile: failed to solve build step")
        )

        self.assertEqual(diagnosis.decision.failure, "container_build_failure")
        self.assertEqual(diagnosis.decision.action, "check_logs")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_handles_port_collision(self) -> None:
        diagnosis = diagnose_observation(
            _observation(stderr_tail="OSError: [Errno 98] Address already in use")
        )

        self.assertEqual(diagnosis.decision.failure, "port_in_use")
        self.assertEqual(diagnosis.decision.action, "check_port")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_default_diagnosis_stops_on_successful_command(self) -> None:
        diagnosis = diagnose_observation(
            _observation(exit_code=0, stdout_tail="ok\n", stderr_tail="")
        )

        self.assertEqual(diagnosis.decision.failure, "command_succeeded")
        self.assertEqual(diagnosis.decision.action, "stop")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_injected_provider_still_takes_precedence(self) -> None:
        provider = MockModelProvider(
            Decision(
                failure="provider_selected",
                action="check_logs",
                confidence=0.91,
                risk="low",
                escalate=False,
                evidence=["provider was explicitly injected"],
            )
        )

        diagnosis = diagnose_observation(
            _observation(stderr_tail="ModuleNotFoundError: No module named 'yaml'"),
            provider=provider,
        )

        self.assertEqual(diagnosis.decision.failure, "provider_selected")
        self.assertEqual(len(provider.calls), 1)


def _observation(
    *,
    exit_code: int = 1,
    stdout_tail: str = "",
    stderr_tail: str = "error: failed",
    runtime: dict[str, object] | None = None,
) -> Observation:
    return Observation(
        command="python -m pytest",
        cwd="/workspace/example",
        exit_code=exit_code,
        stdout_tail=stdout_tail,
        stderr_tail=stderr_tail,
        duration_ms=100,
        source="baseline_test",
        policy_summary="bounded local test observation",
        runtime=runtime or {},
    )


if __name__ == "__main__":
    unittest.main()
