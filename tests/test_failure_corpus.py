from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minerva_kernel.failure_corpus import (
    REQUIRED_M0_CATEGORIES,
    load_failure_cases,
)


class FailureCorpusTests(unittest.TestCase):
    def test_default_m0_slice_loads_and_covers_required_categories(self) -> None:
        cases = load_failure_cases()

        self.assertGreaterEqual(len(cases), 20)
        self.assertTrue(REQUIRED_M0_CATEGORIES.issubset({case.category for case in cases}))
        self.assertEqual(len({case.case_id for case in cases}), len(cases))
        self.assertTrue(all(case.expected_failure for case in cases))
        self.assertTrue(all(case.expected_action for case in cases))
        self.assertTrue(all(case.policy_allowed for case in cases))
        self.assertTrue(all(case.rationale for case in cases))

    def test_loader_rejects_unsupported_action(self) -> None:
        malformed = _valid_case()
        malformed["expected_action"] = "run_command"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cases.json"
            path.write_text(json.dumps([malformed]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unsupported expected_action"):
                load_failure_cases(path)

    def test_loader_rejects_policy_mismatch(self) -> None:
        malformed = _valid_case()
        malformed["policy_expectation"] = {
            "allowed": False,
            "reason": "bad fixture expects a blocked read-only action",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cases.json"
            path.write_text(json.dumps([malformed]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "policy_expectation.allowed"):
                load_failure_cases(path)

    def test_loader_rejects_secret_case_without_redaction_expectation(self) -> None:
        malformed = _valid_case()
        malformed["category"] = "secret-redaction"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cases.json"
            path.write_text(json.dumps([malformed]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "redaction_expectation"):
                load_failure_cases(path)


def _valid_case() -> dict[str, object]:
    return {
        "id": "fixture-python-missing-module",
        "category": "python",
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
        "expected_failure": "missing_python_module",
        "expected_action": "inspect_dependencies",
        "policy_expectation": {
            "allowed": True,
            "reason": "Read-only dependency inspection is allowed.",
        },
        "rationale": "The import error names a missing module.",
    }


if __name__ == "__main__":
    unittest.main()
