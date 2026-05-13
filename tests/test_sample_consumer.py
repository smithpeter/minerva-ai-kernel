from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample-consumer"


class SampleConsumerLayoutTests(unittest.TestCase):
    """The sample-consumer template is meant to be copied into another repo.

    These tests guard the contract: every file the README tells a user to
    copy must exist, be in the expected relative path, and have the shape
    the documentation promises.
    """

    def test_documented_files_exist(self) -> None:
        for relative in (
            "README.md",
            "failing-build.sh",
            "app/sample_app.py",
            ".github/workflows/ci.yml",
            ".github/workflows/minerva-diagnose.yml",
        ):
            with self.subTest(path=relative):
                self.assertTrue((SAMPLE / relative).is_file(), relative)

    def test_failing_build_script_is_executable(self) -> None:
        script = SAMPLE / "failing-build.sh"
        self.assertTrue(os.access(script, os.X_OK), "failing-build.sh must be executable")

    def test_sample_app_imports_nonexistent_package(self) -> None:
        # Use a deliberately-nonexistent package so the failure is
        # reproducible in any environment, including local machines
        # that have pyyaml or similar common packages installed.
        source = (SAMPLE / "app" / "sample_app.py").read_text(encoding="utf-8")
        self.assertIn("minerva_sample_missing_dep", source)
        # Guard against accidentally importing a real package later.
        self.assertNotIn("\nimport yaml", source)

    def test_ci_workflow_uploads_build_log(self) -> None:
        workflow = (SAMPLE / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("bash failing-build.sh", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("name: build-log", workflow)

    def test_diagnose_workflow_uses_minerva_action(self) -> None:
        workflow = (SAMPLE / ".github" / "workflows" / "minerva-diagnose.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("smithpeter/minerva-ai-kernel@", workflow)
        self.assertIn("workflow_run", workflow)
        self.assertIn("conclusion == 'failure'", workflow)
        self.assertIn("log-path: build.log", workflow)

    def test_diagnose_workflow_does_not_auto_repair(self) -> None:
        # The whole point of Minerva is read-only diagnosis. Make sure
        # the template does not accidentally introduce auto-repair
        # patterns when someone copies it.
        workflow = (SAMPLE / ".github" / "workflows" / "minerva-diagnose.yml").read_text(
            encoding="utf-8"
        )
        for forbidden in ("pip install", "git push", "git commit", "gh pr create"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, workflow)


class SampleConsumerRunTests(unittest.TestCase):
    def test_failing_build_actually_fails(self) -> None:
        """The build script must exit non-zero on a clean Python install."""
        result = subprocess.run(
            ["bash", "failing-build.sh"],
            cwd=SAMPLE,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(
            result.returncode,
            0,
            f"failing-build.sh unexpectedly succeeded. stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        combined = result.stdout + result.stderr
        self.assertIn("ModuleNotFoundError", combined)


if __name__ == "__main__":
    unittest.main()
