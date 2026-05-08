from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path

from minerva_kernel import Decision, MockModelProvider
from minerva_kernel.cli import main


@contextlib.contextmanager
def _working_directory(path: str | Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class ObserveCliTests(unittest.TestCase):
    def _provider(self, *, action: str = "stop") -> MockModelProvider:
        return MockModelProvider(
            Decision(
                failure="observed_command",
                action=action,  # type: ignore[arg-type]
                confidence=0.91,
                risk="low",
                escalate=False,
                evidence=["bounded command observation was captured"],
                reason="Provider returned a deterministic observe decision.",
            )
        )

    def _run_observe(
        self, tmpdir: str, args: list[str], provider: MockModelProvider | None = None
    ) -> tuple[str, dict[str, object], Path, MockModelProvider]:
        active_provider = provider or self._provider()
        stdout = io.StringIO()
        with _working_directory(tmpdir), contextlib.redirect_stdout(stdout):
            main(["observe", *args], provider=active_provider)

        output = stdout.getvalue()
        record_path = self._saved_path(output, Path(tmpdir))
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertIsInstance(record, dict)
        return output, record, record_path, active_provider

    def test_observe_successful_command_saves_run_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output, record, record_path, provider = self._run_observe(
                tmpdir,
                ["--", sys.executable, "-c", "print('ok')"],
            )

        self.assertEqual(len(provider.calls), 1)
        self.assertIn("Policy decision: allowed", output)
        self.assertTrue(record_path.name.endswith(".json"))
        self.assertEqual(record["schema_version"], "run.v0")
        self.assertRegex(str(record["created_at"]), r"Z$")
        self.assertEqual(
            record["policy_decision"],
            {"allowed": True, "reason": "allowed by read-only policy"},
        )

        observation = self._mapping(record["observation"])
        self.assertEqual(observation["schema_version"], "observation.v0")
        self.assertEqual(observation["exit_code"], 0)
        self.assertEqual(observation["stdout_tail"], "ok\n")
        self.assertEqual(observation["stderr_tail"], "")
        self.assertEqual(observation["source"], "local_shell")
        self.assertEqual(observation["cwd"], str(Path(tmpdir).resolve()))
        self.assertIn(sys.executable, str(observation["command"]))

        runtime = self._mapping(observation["runtime"])
        self.assertEqual(runtime["network_status"], "unknown")
        self.assertEqual(runtime["timed_out"], False)
        self.assertEqual(runtime["command_found"], True)
        self.assertIn("python", runtime)
        self.assertIn("platform", runtime)

        decision = self._mapping(record["decision"])
        self.assertEqual(decision["schema_version"], "decision.v0")
        self.assertEqual(decision["action"], "stop")

    def test_observe_failing_command_captures_exit_code_and_stderr_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, record, _, _ = self._run_observe(
                tmpdir,
                [
                    "--",
                    sys.executable,
                    "-c",
                    "import sys; print('boom', file=sys.stderr); sys.exit(3)",
                ],
                provider=self._provider(action="inspect_dependencies"),
            )

        observation = self._mapping(record["observation"])
        self.assertEqual(observation["exit_code"], 3)
        self.assertEqual(observation["stdout_tail"], "")
        self.assertEqual(observation["stderr_tail"], "boom\n")

    def test_observe_timeout_records_bounded_timeout_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, record, _, _ = self._run_observe(
                tmpdir,
                [
                    "--timeout",
                    "0.05",
                    "--",
                    sys.executable,
                    "-c",
                    "import time; time.sleep(1)",
                ],
                provider=self._provider(action="check_logs"),
            )

        observation = self._mapping(record["observation"])
        runtime = self._mapping(observation["runtime"])
        self.assertEqual(observation["exit_code"], 124)
        self.assertIn("timed out", str(observation["stderr_tail"]))
        self.assertEqual(runtime["timed_out"], True)
        self.assertEqual(runtime["error_type"], "TimeoutExpired")
        self.assertEqual(runtime["timeout_seconds"], 0.05)

    def test_observe_command_not_found_records_127_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, record, _, _ = self._run_observe(
                tmpdir,
                ["--", "minerva-command-that-does-not-exist-12345"],
                provider=self._provider(action="check_command_exists"),
            )

        observation = self._mapping(record["observation"])
        runtime = self._mapping(observation["runtime"])
        self.assertEqual(observation["exit_code"], 127)
        self.assertIn("command not found", str(observation["stderr_tail"]))
        self.assertEqual(runtime["command_found"], False)
        self.assertEqual(runtime["error_type"], "FileNotFoundError")

    def test_observe_redacts_model_prompt_and_saved_run_record(self) -> None:
        token = "abcdefghijklmnopqrstuvwxyz123456"
        with tempfile.TemporaryDirectory() as tmpdir:
            _, record, record_path, provider = self._run_observe(
                tmpdir,
                [
                    "--",
                    sys.executable,
                    "-c",
                    f"print('Authorization: Bearer {token}')",
                ],
                provider=self._provider(action="check_logs"),
            )
            record_text = record_path.read_text(encoding="utf-8")

        prompt_text = json.dumps(provider.calls)
        self.assertNotIn(token, prompt_text)
        self.assertNotIn(token, record_text)
        self.assertIn("[REDACTED:bearer_token]", prompt_text)
        self.assertIn("[REDACTED:bearer_token]", record_text)

        observation = self._mapping(record["observation"])
        redactions = self._mapping(observation["redactions"])
        self.assertGreaterEqual(int(redactions["count"]), 1)
        self.assertEqual(redactions["types"], ["bearer_token"])
        self.assertIn("redactions", record)

    def _saved_path(self, output: str, root: Path) -> Path:
        for line in output.splitlines():
            if line.startswith("Saved: "):
                saved = Path(line.removeprefix("Saved: "))
                return saved if saved.is_absolute() else root / saved
        self.fail(f"missing Saved line in output: {output}")

    def _mapping(self, value: object) -> dict[str, object]:
        self.assertIsInstance(value, dict)
        return value  # type: ignore[return-value]


if __name__ == "__main__":
    unittest.main()
