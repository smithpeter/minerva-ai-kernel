from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "action.yml"
README = ROOT / "README.md"
DEMO = ROOT / "docs" / "five-minute-demo.md"


class GitHubActionMetadataTests(unittest.TestCase):
    def test_action_metadata_declares_report_only_ci_diagnosis(self) -> None:
        text = ACTION.read_text(encoding="utf-8")

        for expected in (
            "name: Minerva Failure Diagnosis",
            "log-path:",
            "job-name:",
            "tail-chars:",
            "fail-on-policy-block:",
            "minerva ci-analyze",
            "GITHUB_STEP_SUMMARY",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_action_does_not_execute_minerva_actions(self) -> None:
        text = ACTION.read_text(encoding="utf-8")

        self.assertNotIn("minerva execute-action", text)
        self.assertNotIn("minerva observe --", text)

    def test_readme_links_five_minute_demo_and_action_docs(self) -> None:
        text = README.read_text(encoding="utf-8")

        self.assertIn("docs/five-minute-demo.md", text)
        self.assertIn("docs/github-action.md", text)

    def test_demo_uses_checked_in_log_fixture(self) -> None:
        text = DEMO.read_text(encoding="utf-8")

        self.assertIn("examples/logs/missing-dependency.log", text)
        self.assertIn("minerva ci-analyze", text)


if __name__ == "__main__":
    unittest.main()
