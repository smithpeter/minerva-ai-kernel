from __future__ import annotations

import unittest
from pathlib import Path


class CiSmokeWorkflowTests(unittest.TestCase):
    def test_smoke_workflow_publishes_minerva_evidence_without_masking_gate(self) -> None:
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "ci-smoke.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn('python-version: "3.11"', workflow)
        self.assertNotIn('python-version: "3.x"', workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("minerva observe -- bash -c", workflow)
        self.assertIn(
            "python3 -m compileall minerva_kernel && "
            "python3 -m unittest discover -s tests && "
            "python3 -m minerva_kernel.eval_smoke",
            workflow,
        )
        self.assertIn(
            'minerva render-ci-summary "$run_record" >> "$GITHUB_STEP_SUMMARY"',
            workflow,
        )
        self.assertIn(
            'minerva render-ci-artifact "$run_record" > minerva-ci-run.json',
            workflow,
        )
        self.assertIn(
            'minerva verify --diff "$verify_diff" --run --format json '
            "--output minerva-merge-evidence.json",
            workflow,
        )
        self.assertIn(
            'minerva render-merge-evidence-summary minerva-merge-evidence.json',
            workflow,
        )
        self.assertIn("minerva-merge-evidence", workflow)
        self.assertIn(
            '["observation"]["exit_code"]',
            workflow,
        )
        self.assertIn('exit "$observed_status"', workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
