from __future__ import annotations

import contextlib
import io
import json
import unittest

from minerva_kernel.cli import main as cli_main
from minerva_kernel.verify_eval import (
    build_verify_eval_report,
    load_verify_cases,
    render_verify_eval_markdown,
)


class VerifyEvalTests(unittest.TestCase):
    def test_verify_cases_fixture_has_first_25_cases(self) -> None:
        cases = load_verify_cases()

        self.assertEqual(len(cases), 25)
        self.assertEqual(len({case["id"] for case in cases}), 25)

    def test_verify_eval_reports_useful_merge_evidence_rate(self) -> None:
        report = build_verify_eval_report()

        metric = report["metrics"]["useful_merge_evidence_rate"]
        self.assertEqual(report["schema_version"], "verify_eval_report.v0")
        self.assertEqual(metric["useful"], 25)
        self.assertEqual(metric["total"], 25)
        self.assertEqual(metric["rate"], 1.0)
        self.assertTrue(all(result["passed"] for result in report["results"]))

    def test_markdown_render_mentions_metric(self) -> None:
        markdown = render_verify_eval_markdown(build_verify_eval_report())

        self.assertIn("# Minerva Verify Eval Report", markdown)
        self.assertIn("Useful Merge Evidence Rate", markdown)
        self.assertIn("25/25 (100.0%)", markdown)

    def test_cli_verify_eval_report_outputs_json(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            cli_main(["verify-eval-report"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], "verify_eval_report.v0")
        self.assertEqual(
            payload["metrics"]["useful_merge_evidence_rate"]["rate"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()

