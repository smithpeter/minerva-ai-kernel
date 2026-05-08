from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from minerva_kernel.eval_smoke import DEFAULT_CASES_PATH, run_smoke_eval


class EvalSmokeTests(unittest.TestCase):
    def test_default_smoke_corpus_passes(self) -> None:
        stdout = io.StringIO()

        summary = run_smoke_eval(DEFAULT_CASES_PATH, stream=stdout)

        self.assertEqual(summary.total, 5)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(summary.passed, 5)
        out = stdout.getvalue()
        self.assertIn("Minerva eval smoke v0", out)
        self.assertIn("Cases: 5/5 passed, 0 failed", out)
        self.assertIn("Safe Recovery Decision Rate: 5/5 (100.0%)", out)
        self.assertIn("PASS dependency-missing-python-module", out)
        self.assertIn("PASS log-secret-redaction", out)

    def test_runner_reports_failing_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_path = Path(tmpdir) / "cases.jsonl"
            cases_path.write_text(json.dumps(_failing_case()) + "\n", encoding="utf-8")
            stdout = io.StringIO()

            summary = run_smoke_eval(cases_path, stream=stdout)

        self.assertEqual(summary.total, 1)
        self.assertEqual(summary.failed, 1)
        self.assertFalse(summary.results[0].passed)
        out = stdout.getvalue()
        self.assertIn("FAIL wrong-action", out)
        self.assertIn("expected action inspect_dependencies, got check_logs", out)


def _failing_case() -> dict[str, object]:
    return {
        "id": "wrong-action",
        "observation": {
            "schema_version": "observation.v0",
            "command": "python3 -m unittest",
            "cwd": "/workspace/minerva-ai-kernel",
            "exit_code": 1,
            "stdout_tail": "",
            "stderr_tail": "ModuleNotFoundError: No module named 'requests'",
            "duration_ms": 250,
            "source": "local_shell",
            "policy_summary": "non-destructive command; full logs omitted",
        },
        "decision": {
            "failure": "missing_python_module",
            "action": "check_logs",
            "confidence": 0.9,
            "risk": "low",
            "escalate": False,
            "evidence": ["stderr contains ModuleNotFoundError"],
        },
        "expected": {
            "failure": "missing_python_module",
            "action": "inspect_dependencies",
            "policy_allowed": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
