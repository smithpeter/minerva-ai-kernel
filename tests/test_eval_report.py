from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path

from minerva_kernel.cli import main as cli_main
from minerva_kernel.eval_report import (
    build_m1_eval_report,
    render_m1_eval_report,
    render_report_json,
    render_report_markdown,
)


ROOT = Path(__file__).resolve().parents[1]


class EvalReportTests(unittest.TestCase):
    def test_default_report_contains_m1_metrics(self) -> None:
        report = build_m1_eval_report()

        self.assertEqual(report["schema_version"], "m1_eval_report.v0")
        self.assertEqual(
            report["fixtures"],
            {
                "smoke_cases": "evals/smoke_cases.jsonl",
                "failure_corpus": "evals/failure_cases_m0_slice.json",
            },
        )
        self.assertEqual(report["targets"]["cases_per_required_category"], 15)

        metrics = report["metrics"]
        self.assertEqual(metrics["json_validity"]["valid"], 117)
        self.assertEqual(metrics["json_validity"]["total"], 117)
        self.assertEqual(metrics["failure_label_accuracy"]["correct"], 5)
        self.assertEqual(metrics["failure_label_accuracy"]["total"], 5)
        self.assertEqual(metrics["safe_recovery_decision_rate"]["correct"], 5)
        self.assertEqual(metrics["safe_recovery_decision_rate"]["total"], 5)
        self.assertEqual(metrics["escalation_quality"]["false_positives"], 0)
        self.assertEqual(metrics["escalation_quality"]["false_negatives"], 0)
        self.assertEqual(metrics["dangerous_action_rate"]["dangerous"], 0)
        self.assertEqual(metrics["dangerous_action_rate"]["total"], 117)

        corpus = report["corpus"]
        self.assertEqual(corpus["total_cases"], 112)
        self.assertEqual(corpus["total_gap_to_target"], 68)
        self.assertEqual(corpus["category_counts"]["python"], 9)
        self.assertEqual(corpus["category_counts"]["git"], 10)
        self.assertEqual(corpus["category_gaps_to_target"]["python"], 6)
        self.assertEqual(corpus["category_gaps_to_target"]["git"], 5)

    def test_json_rendering_is_valid_and_repeatable(self) -> None:
        report = build_m1_eval_report()

        first = render_report_json(report)
        second = render_report_json(build_m1_eval_report())

        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["schema_version"], "m1_eval_report.v0")
        self.assertEqual(payload["metrics"]["json_validity"]["rate"], 1.0)

    def test_markdown_rendering_matches_checked_in_report(self) -> None:
        generated = render_report_markdown(build_m1_eval_report())
        checked_in = (ROOT / "evals" / "m1_eval_report.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(generated, checked_in)
        self.assertIn("| Dangerous action rate | 0/117 (0.0%) |", generated)
        self.assertIn("Total gap to target: 68 cases.", generated)

    def test_module_render_supports_markdown_format(self) -> None:
        output = render_m1_eval_report(output_format="markdown")

        self.assertTrue(output.startswith("# M1 Eval Report\n"))
        self.assertIn("| JSON validity | 5/5 smoke decisions", output)

    def test_minerva_cli_eval_report_outputs_json(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            cli_main(["eval-report"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], "m1_eval_report.v0")
        self.assertEqual(
            payload["metrics"]["safe_recovery_decision_rate"]["rate"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
