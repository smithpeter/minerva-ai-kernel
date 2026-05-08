from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from minerva_kernel import Decision, Minerva, MockModelProvider, Observation


class SdkExampleTests(unittest.TestCase):
    def test_minerva_facade_returns_decision_with_policy_result(self) -> None:
        kernel = Minerva(
            provider=MockModelProvider(
                Decision(
                    failure="missing_dependency",
                    action="inspect_dependencies",
                    confidence=0.84,
                    risk="low",
                    escalate=False,
                    evidence=["stderr contains ModuleNotFoundError"],
                )
            )
        )

        diagnosis = kernel.decide(_observation())

        self.assertEqual(diagnosis.decision.action, "inspect_dependencies")
        self.assertTrue(diagnosis.policy_decision.allowed)
        self.assertEqual(
            diagnosis.policy_decision.reason,
            "allowed by read-only policy",
        )

    def test_minerva_facade_loads_observation_file(self) -> None:
        kernel = Minerva(
            provider=MockModelProvider(
                Decision(
                    failure="missing_command",
                    action="check_command_exists",
                    confidence=0.91,
                    risk="low",
                    escalate=False,
                    evidence=["stderr contains command not found"],
                )
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "observation.json"
            path.write_text(json.dumps(_observation().to_dict()), encoding="utf-8")
            diagnosis = kernel.decide_file(path)

        self.assertEqual(diagnosis.decision.action, "check_command_exists")
        self.assertTrue(diagnosis.policy_decision.allowed)

    def test_minimal_sdk_example_runs_locally(self) -> None:
        payload = _run_example("examples/minimal_sdk_decision.py")

        self.assertEqual(payload["decision"]["action"], "inspect_dependencies")
        self.assertTrue(payload["policy_decision"]["allowed"])
        self.assertEqual(payload["execution"]["state"], "not_executed")

    def test_agent_tool_failure_example_runs_locally(self) -> None:
        payload = _run_example("examples/agent_tool_failure.py")

        self.assertEqual(payload["observation"]["source"], "agent_tool_example")
        self.assertEqual(payload["decision"]["action"], "check_command_exists")
        self.assertTrue(payload["policy_decision"]["allowed"])
        self.assertEqual(payload["execution"]["state"], "not_executed")


def _run_example(path: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, path],
        capture_output=True,
        check=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise AssertionError("example output must be a JSON object")
    return payload


def _observation() -> Observation:
    return Observation(
        command="python3 -m unittest discover -s tests",
        cwd="/workspace/example-project",
        exit_code=1,
        stdout_tail="",
        stderr_tail="ModuleNotFoundError: No module named 'example_package'",
        duration_ms=742,
        source="sdk_test",
        policy_summary="test observation with bounded stderr and no credentials",
    )


if __name__ == "__main__":
    unittest.main()
