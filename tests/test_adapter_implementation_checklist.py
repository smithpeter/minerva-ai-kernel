from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "adapter-implementation-checklist.md"
REPORTING = ROOT / "docs" / "adapter-event-reporting.md"


class AdapterImplementationChecklistTests(unittest.TestCase):
    def test_checklist_contains_required_safety_boundaries(self) -> None:
        text = CHECKLIST.read_text(encoding="utf-8")

        required_terms = [
            "observation.v0",
            "Redact before model input",
            "policy_decision.allowed",
            "adapter_executes_actions=false",
            "execution.state=not_executed",
            "Do not override the original CI job or platform failure status",
            "no hosted Minerva control plane or remote model is required",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_checklist_names_required_adapter_tests(self) -> None:
        text = CHECKLIST.read_text(encoding="utf-8")

        for phrase in (
            "valid host event becomes valid `observation.v0`",
            "secret-like input is redacted before persistence",
            "policy-blocked Minerva response is reported with block reason",
            "Minerva-unavailable path preserves the original host failure",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_reporting_guide_links_checklist(self) -> None:
        text = REPORTING.read_text(encoding="utf-8")

        self.assertIn("adapter-implementation-checklist.md", text)


if __name__ == "__main__":
    unittest.main()
