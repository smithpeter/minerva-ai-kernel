from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from minerva_kernel import Decision, MockModelProvider
from minerva_kernel.cli import main


class CliTests(unittest.TestCase):
    def _write_observation(self, directory: str, **overrides: object) -> Path:
        payload: dict[str, object] = {
            "schema_version": "observation.v0",
            "command": "pytest tests/test_cli.py",
            "cwd": "/workspace/minerva-ai-kernel",
            "exit_code": 1,
            "stdout_tail": "",
            "stderr_tail": "ModuleNotFoundError: No module named 'minerva_kernel'",
            "duration_ms": 931,
            "source": "local_shell",
            "policy_summary": "non-destructive command; full logs omitted",
        }
        payload.update(overrides)
        path = Path(directory) / "failure.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _allowed_provider(self) -> MockModelProvider:
        return MockModelProvider(
            Decision(
                failure="missing_dependency",
                action="inspect_dependencies",
                confidence=0.82,
                risk="low",
                escalate=False,
                evidence=["stderr contains ModuleNotFoundError"],
            )
        )

    def test_cli_help(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                main([])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)

        self.assertIn("CPU-local failure interpreter", stdout.getvalue())

    def test_cli_policy_check_shows_block_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "decision.json"
            payload_path.write_text(
                json.dumps({"action": "check_logs", "command": "rm -rf /tmp/example"}),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as raised:
                    main(["policy-check", str(payload_path)])

        self.assertEqual(raised.exception.code, 2)
        out = stdout.getvalue()
        self.assertIn("Policy decision: blocked", out)
        self.assertIn("Reason: blocked destructive command attempt", out)

    def test_cli_diagnose_outputs_successful_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = self._write_observation(tmpdir)
            provider = self._allowed_provider()

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(["diagnose", str(payload_path)], provider=provider)

        out = stdout.getvalue()
        self.assertIn("Failure: missing_dependency", out)
        self.assertIn("Action: inspect_dependencies", out)
        self.assertIn("Confidence: 0.82", out)
        self.assertIn("Risk: low", out)
        self.assertIn("Escalation: false", out)
        self.assertIn("Policy decision: allowed", out)
        self.assertIn("Policy decision reason: allowed by read-only policy", out)
        self.assertEqual(len(provider.calls), 1)

    def test_cli_diagnose_rejects_invalid_observation_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "failure.json"
            payload_path.write_text(
                json.dumps({"schema_version": "decision.v0"}),
                encoding="utf-8",
            )

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    main(["diagnose", str(payload_path)], provider=self._allowed_provider())

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("unsupported observation schema_version", stderr.getvalue())

    def test_cli_diagnose_exits_nonzero_for_policy_blocked_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = self._write_observation(tmpdir)
            provider = MockModelProvider(
                Decision(
                    failure="ambiguous_runtime_failure",
                    action="check_logs",
                    confidence=0.91,
                    risk="medium",
                    escalate=False,
                    evidence=["failure requires broader inspection"],
                )
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as raised:
                    main(["diagnose", str(payload_path)], provider=provider)

        self.assertEqual(raised.exception.code, 2)
        out = stdout.getvalue()
        self.assertIn("Policy decision: blocked", out)
        self.assertIn("Policy decision reason: risk is medium", out)

    def test_cli_diagnose_reports_redaction_summary_and_sends_redacted_prompt(self) -> None:
        token = "abcdefghijklmnopqrstuvwxyz123456"
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = self._write_observation(
                tmpdir,
                command=f"curl -H 'Authorization: Bearer {token}'",
            )
            provider = self._allowed_provider()

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(["diagnose", str(payload_path)], provider=provider)

        self.assertIn(
            "Redaction summary: count=1 types=bearer_token",
            stdout.getvalue(),
        )
        prompt_text = json.dumps(provider.calls)
        self.assertNotIn(token, prompt_text)
        self.assertIn("[REDACTED:bearer_token]", prompt_text)

    def test_cli_execute_action_outputs_read_only_executor_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            decision_path = Path(tmpdir) / "decision.json"
            decision_path.write_text(
                json.dumps(
                    Decision(
                        failure="missing_dependency",
                        action="inspect_dependencies",
                        confidence=0.91,
                        risk="low",
                        escalate=False,
                        evidence=["stderr contains ModuleNotFoundError"],
                    ).to_dict()
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as raised:
                    main(["execute-action", str(decision_path), "--cwd", tmpdir])

        self.assertEqual(raised.exception.code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], "observation.v0")
        self.assertEqual(payload["source"], "kernel_executor")
        self.assertEqual(payload["command"], "executor:inspect_dependencies")
        self.assertIn("pyproject.toml", payload["stdout_tail"])
        self.assertEqual(payload["runtime"]["policy_allowed"], True)

    def test_cli_execute_action_exits_nonzero_when_policy_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            decision_path = Path(tmpdir) / "decision.json"
            decision_path.write_text(
                json.dumps(
                    Decision(
                        failure="needs_escalation",
                        action="ask_user",
                        confidence=0.91,
                        risk="low",
                        escalate=True,
                        evidence=["operator needed"],
                    ).to_dict()
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as raised:
                    main(["execute-action", str(decision_path), "--cwd", tmpdir])

        self.assertEqual(raised.exception.code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["source"], "kernel_executor")
        self.assertEqual(payload["runtime"]["policy_allowed"], False)
        self.assertIn("policy blocked executor action", payload["stderr_tail"])


if __name__ == "__main__":
    unittest.main()
