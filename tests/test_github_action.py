from __future__ import annotations

import json
import unittest
from pathlib import Path


class MinervaGithubActionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_action_metadata_is_valid_and_declares_required_inputs(self) -> None:
        metadata_path = self.root / "action" / "action.yml"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata["runs"]["using"], "composite")
        self.assertEqual(
            set(metadata["inputs"]),
            {"command", "summary-path", "artifact-name", "redaction-mode"},
        )
        self.assertTrue(metadata["inputs"]["command"]["required"])
        self.assertEqual(
            metadata["inputs"]["summary-path"]["default"],
            "minerva-ci-summary.md",
        )
        self.assertEqual(
            metadata["inputs"]["artifact-name"]["default"],
            "minerva-ci-evidence",
        )
        self.assertEqual(metadata["inputs"]["redaction-mode"]["default"], "strict")

        steps = metadata["runs"]["steps"]
        self.assertIn("actions/setup-python@v5", self._step_uses(steps))
        self.assertIn("actions/upload-artifact@v4", self._step_uses(steps))

    def test_action_wraps_observe_and_preserves_diagnostic_only_boundary(self) -> None:
        metadata = json.loads(
            (self.root / "action" / "action.yml").read_text(encoding="utf-8")
        )
        scripts = "\n".join(
            step.get("run", "") for step in metadata["runs"]["steps"] if "run" in step
        )

        self.assertIn('minerva observe -- bash -lc "$MINERVA_COMMAND"', scripts)
        self.assertIn('minerva render-ci-summary "$run_record"', scripts)
        self.assertIn('minerva render-ci-artifact "$run_record"', scripts)
        self.assertIn('json.load(handle)["observation"]["exit_code"]', scripts)
        self.assertNotIn("minerva execute", scripts)
        self.assertNotIn("minerva remediate", scripts)
        self.assertNotIn("apply_patch", scripts)
        self.assertNotIn("run_safe_command", scripts)

    def test_demo_workflow_uses_published_action_with_trivial_command(self) -> None:
        workflow = (self.root / "examples" / "minerva-action-demo.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("uses: smithpeter/minerva-action@v0", workflow)
        self.assertIn("command: python3 -c", workflow)
        self.assertIn("summary-path: minerva-ci-summary.md", workflow)
        self.assertIn("artifact-name: minerva-ci-evidence", workflow)
        self.assertIn("redaction-mode: strict", workflow)

    def _step_uses(self, steps: list[dict[str, object]]) -> set[str]:
        return {str(step["uses"]) for step in steps if "uses" in step}


if __name__ == "__main__":
    unittest.main()
