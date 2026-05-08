from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-release-readiness.py"


def load_checker_module():
    spec = importlib.util.spec_from_file_location("check_release_readiness", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load release readiness checker")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseReadinessCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = load_checker_module()

    def test_skip_external_mode_is_local_and_public_safe(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--skip-external",
                "--install-backend",
                "skip",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("[local_checkout] pass", completed.stdout)
        self.assertIn("[local_install_backend] skipped", completed.stdout)
        self.assertIn("[github_actions] skipped", completed.stdout)
        self.assertIn("[domain_dns] skipped", completed.stdout)
        self.assertIn("overall=pass", completed.stdout)
        self.assertNotIn(str(ROOT), completed.stdout)
        self.assertTrue(
            all(len(line) <= 260 for line in completed.stdout.splitlines()),
            completed.stdout,
        )

    def test_github_actions_result_passes_only_completed_success_runs(self) -> None:
        result = self.checker.github_actions_result_from_runs(
            [
                {
                    "name": "ci",
                    "status": "completed",
                    "conclusion": "success",
                    "updated_at": "2026-05-08T00:00:00Z",
                    "html_url": "https://github.com/smithpeter/minerva-ai-kernel/actions/runs/1",
                }
            ],
            commit="abc123",
        )

        self.assertEqual(result.status, "pass")
        self.assertEqual(self.checker.readiness_exit_code([result]), 0)

    def test_github_actions_result_fails_pending_or_red_runs(self) -> None:
        result = self.checker.github_actions_result_from_runs(
            [
                {
                    "name": "ci",
                    "status": "completed",
                    "conclusion": "failure",
                    "updated_at": "2026-05-08T00:00:00Z",
                    "html_url": "https://github.com/smithpeter/minerva-ai-kernel/actions/runs/2",
                },
                {
                    "name": "lint",
                    "status": "in_progress",
                    "conclusion": None,
                    "updated_at": "2026-05-08T00:01:00Z",
                    "html_url": "https://github.com/smithpeter/minerva-ai-kernel/actions/runs/3",
                },
            ],
            commit="abc123",
        )

        self.assertEqual(result.status, "fail")
        self.assertEqual(self.checker.readiness_exit_code([result]), 1)
        self.assertIn("all returned runs must be completed", "\n".join(result.details))

    def test_install_backend_result_passes_when_build_meta_imports(self) -> None:
        result = self.checker.install_backend_result_from_probe(
            subprocess.CompletedProcess(
                ["python", "-c", "probe"],
                0,
                stdout='{"importable": true, "python_version": "3.11.9"}',
                stderr="",
            ),
            mode="current",
        )

        self.assertEqual(result.status, "pass")
        self.assertEqual(self.checker.readiness_exit_code([result]), 0)
        self.assertIn("setuptools.build_meta_importable=yes", result.details)
        self.assertIn(
            (
                "next_action=offline editable install can use "
                "--no-build-isolation with this local build backend available"
            ),
            result.details,
        )

    def test_install_backend_result_fails_when_build_meta_is_missing(self) -> None:
        result = self.checker.install_backend_result_from_probe(
            subprocess.CompletedProcess(
                ["python", "-c", "probe"],
                0,
                stdout=(
                    '{"error": "ModuleNotFoundError", "importable": false, '
                    '"message": "No module named setuptools", '
                    '"python_version": "3.14.0"}'
                ),
                stderr="",
            ),
            mode="fresh-venv",
        )

        self.assertEqual(result.status, "fail")
        self.assertEqual(self.checker.readiness_exit_code([result]), 1)
        self.assertIn("setuptools.build_meta_importable=no", result.details)
        self.assertIn("error=ModuleNotFoundError", result.details)
        self.assertIn(
            (
                "next_action=use a local interpreter or venv that already "
                "provides setuptools.build_meta, or seed setuptools from an "
                "approved local wheel/cache before rerunning; do not download "
                "dependencies during this readiness check"
            ),
            result.details,
        )

    def test_install_backend_check_can_be_skipped(self) -> None:
        result = self.checker.check_install_backend(
            mode="skip",
            python=sys.executable,
            timeout=1.0,
        )

        self.assertEqual(result.status, "skipped")
        self.assertEqual(self.checker.readiness_exit_code([result]), 0)
        self.assertIn("skipped by --install-backend skip", result.details)


if __name__ == "__main__":
    unittest.main()
