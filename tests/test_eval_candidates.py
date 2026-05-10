from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from minerva_kernel.cli import main
from minerva_kernel.eval_candidates import (
    EVAL_CANDIDATE_SCHEMA_VERSION,
    build_eval_candidate_from_run,
    render_eval_candidates_jsonl,
)
from minerva_kernel.observe import build_run_record
from minerva_kernel.policy import validate_action
from minerva_kernel.types import Decision, Observation


class EvalCandidateTests(unittest.TestCase):
    def test_build_eval_candidate_from_run_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = _write_run_record(Path(tmpdir) / "run.json")

            candidate = build_eval_candidate_from_run(run_path)

        self.assertEqual(candidate["schema_version"], EVAL_CANDIDATE_SCHEMA_VERSION)
        self.assertEqual(candidate["review"]["status"], "needs_human_review")
        self.assertEqual(candidate["review"]["approved_for_corpus"], False)
        case = candidate["case"]
        self.assertEqual(case["category"], "unreviewed")
        self.assertEqual(case["suggested_expected"]["failure"], "missing_dependency")
        self.assertEqual(case["suggested_expected"]["action"], "inspect_dependencies")
        self.assertEqual(case["suggested_expected"]["safe_recovery_eligible"], True)
        self.assertEqual(case["policy_decision"]["allowed"], True)

    def test_render_eval_candidates_jsonl_redacts_secret_material(self) -> None:
        token = "abcdefghijklmnopqrstuvwxyz123456"
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = _write_run_record(
                Path(tmpdir) / "run.json",
                stderr_tail=f"Authorization: Bearer {token}",
            )

            rendered = render_eval_candidates_jsonl([run_path])

        payload = json.loads(rendered)
        self.assertEqual(payload["schema_version"], EVAL_CANDIDATE_SCHEMA_VERSION)
        self.assertNotIn(token, rendered)
        self.assertIn("[REDACTED:bearer_token]", rendered)
        self.assertEqual(payload["redactions"]["types"], ["bearer_token"])

    def test_invalid_run_record_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = Path(tmpdir) / "bad.json"
            run_path.write_text(
                json.dumps({"schema_version": "observation.v0"}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "run.v0"):
                build_eval_candidate_from_run(run_path)

    def test_cli_renders_eval_candidate_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = _write_run_record(Path(tmpdir) / "run.json")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(["render-eval-candidates", str(run_path)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], EVAL_CANDIDATE_SCHEMA_VERSION)


def _write_run_record(
    path: Path,
    *,
    stderr_tail: str = "ModuleNotFoundError: No module named yaml",
) -> Path:
    observation = Observation(
        command="python3 -m unittest",
        cwd="/workspace/minerva-ai-kernel",
        exit_code=1,
        stdout_tail="",
        stderr_tail=stderr_tail,
        duration_ms=310,
        source="local_shell",
        policy_summary="test fixture",
    )
    decision = Decision(
        failure="missing_dependency",
        action="inspect_dependencies",
        confidence=0.91,
        risk="low",
        escalate=False,
        evidence=["stderr contains ModuleNotFoundError"],
    )
    record = build_run_record(
        created_at="2026-05-10T000000Z",
        observation=observation,
        decision=decision,
        policy_decision=validate_action(decision),
        redactions=None,
    )
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
