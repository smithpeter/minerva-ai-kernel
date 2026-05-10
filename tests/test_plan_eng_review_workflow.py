from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PlanEngReviewWorkflowTests(unittest.TestCase):
    def test_workflow_check_passes(self) -> None:
        completed = subprocess.run(
            ["bash", "scripts/check-plan-eng-review.sh"],
            capture_output=True,
            check=True,
            cwd=ROOT,
            text=True,
        )

        self.assertIn("schema_version=plan_eng_review_check.v0", completed.stdout)
        self.assertIn("ready=true", completed.stdout)
        self.assertIn("failures=0", completed.stdout)

    def test_task_template_keeps_plan_eng_review_block(self) -> None:
        template = (ROOT / "docs" / "ai-team-task-template.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Plan-Eng Review", template)
        self.assertIn("### Architecture / Flow", template)
        self.assertIn("### Failure Modes", template)
        self.assertIn("No critical Plan-Eng failure-mode gap remains open.", template)


if __name__ == "__main__":
    unittest.main()
