from __future__ import annotations

import unittest

from minerva_kernel import Observation


class ObservationSchemaTests(unittest.TestCase):
    def test_observation_minimal_example(self) -> None:
        observation = Observation(
            command="python3 -m compileall minerva_kernel",
            cwd="/workspace/minerva-ai-kernel",
            exit_code=0,
            stdout_tail="Listing 'minerva_kernel'...",
            stderr_tail="",
            duration_ms=120,
            source="local_shell",
            policy_summary="validated before execution",
        )

        self.assertEqual(
            observation.to_dict(),
            {
                "schema_version": "observation.v0",
                "command": "python3 -m compileall minerva_kernel",
                "cwd": "/workspace/minerva-ai-kernel",
                "exit_code": 0,
                "stdout_tail": "Listing 'minerva_kernel'...",
                "stderr_tail": "",
                "duration_ms": 120,
                "source": "local_shell",
                "policy_summary": "validated before execution",
            },
        )

    def test_observation_recommended_example_with_runtime_metadata(self) -> None:
        observation = Observation(
            command="pytest tests/test_cli.py",
            cwd="/workspace/minerva-ai-kernel",
            exit_code=1,
            stdout_tail="",
            stderr_tail="ModuleNotFoundError: No module named 'minerva_kernel'",
            duration_ms=931,
            source="local_shell",
            policy_summary="non-destructive command; full logs omitted",
            runtime={
                "python": "3.14.0",
                "platform": "darwin",
                "network_status": "unknown",
            },
        )

        payload = observation.to_dict()

        self.assertEqual(payload["schema_version"], "observation.v0")
        self.assertEqual(payload["stdout_tail"], "")
        self.assertTrue(payload["stderr_tail"].startswith("ModuleNotFoundError"))
        self.assertEqual(
            payload["runtime"],
            {
                "python": "3.14.0",
                "platform": "darwin",
                "network_status": "unknown",
            },
        )
        self.assertEqual(observation.network_status, "unknown")

    def test_observation_rejects_negative_duration(self) -> None:
        with self.assertRaisesRegex(ValueError, "duration_ms"):
            Observation(
                command="pytest",
                cwd="/workspace/minerva-ai-kernel",
                exit_code=1,
                stdout_tail="",
                stderr_tail="failed",
                duration_ms=-1,
                source="local_shell",
                policy_summary="validated before execution",
            )

    def test_observation_to_dict_redacts_saved_record(self) -> None:
        observation = Observation(
            command="curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456'",
            cwd="/workspace/minerva-ai-kernel",
            exit_code=1,
            stdout_tail="",
            stderr_tail="",
            duration_ms=120,
            source="local_shell",
            policy_summary="validated before execution",
        )

        payload = observation.to_dict()

        self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", str(payload))
        self.assertEqual(payload["redactions"]["count"], 1)
        self.assertEqual(payload["redactions"]["types"], ["bearer_token"])


if __name__ == "__main__":
    unittest.main()
