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

    def test_domain_https_result_passes_minerva_brand_signal(self) -> None:
        result = self.checker.domain_https_result_from_response(
            domain="minervakernel.com",
            status_code=200,
            final_url="https://minervakernel.com/",
            content_type="text/html; charset=utf-8",
            body=(
                b"<html><head><title>Minerva AI Kernel</title></head>"
                b"<body>CPU-local failure interpreter for CI/CD.</body></html>"
            ),
        )

        self.assertEqual(result.status, "pass")
        self.assertEqual(self.checker.readiness_exit_code([result]), 0)
        details = "\n".join(result.details)
        self.assertIn("brand_guard=pass", details)
        self.assertIn("minerva_signals=", details)
        self.assertIn("rejected_markers=none", details)

    def test_domain_https_result_fails_without_minerva_brand_signal(self) -> None:
        result = self.checker.domain_https_result_from_response(
            domain="minervakernel.com",
            status_code=200,
            final_url="https://minervakernel.com/",
            content_type="text/html",
            body=b"<html><head><title>Coming Soon</title></head><body>Hosted page.</body></html>",
        )

        self.assertEqual(result.status, "fail")
        self.assertEqual(self.checker.readiness_exit_code([result]), 1)
        details = "\n".join(result.details)
        self.assertIn("brand_guard=fail", details)
        self.assertIn("minerva_signals=missing", details)

    def test_domain_https_result_rejects_voxsign_brand_marker(self) -> None:
        result = self.checker.domain_https_result_from_response(
            domain="minervakernel.com",
            status_code=200,
            final_url="https://minervakernel.com/",
            content_type="text/html",
            body=(
                b"<html><head><title>VoxSign</title></head>"
                b"<body>VoxSign preview for Minerva.</body></html>"
            ),
        )

        self.assertEqual(result.status, "fail")
        self.assertEqual(self.checker.readiness_exit_code([result]), 1)
        details = "\n".join(result.details)
        self.assertIn("brand_guard=fail", details)
        self.assertIn("rejected_markers=voxsign", details)

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

    def test_install_backend_auto_selects_first_passing_candidate(self) -> None:
        candidates = (
            self.checker.PythonCandidate("python-old", "/fake/python-old"),
            self.checker.PythonCandidate("python-good", "/fake/python-good"),
            self.checker.PythonCandidate("python-later", "/fake/python-later"),
        )
        probes = {
            "/fake/python-old": subprocess.CompletedProcess(
                ["python-old", "-c", "probe"],
                0,
                stdout=(
                    '{"error": "ModuleNotFoundError", "importable": false, '
                    '"message": "No module named setuptools", '
                    '"python_version": "3.14.0"}'
                ),
                stderr="",
            ),
            "/fake/python-good": subprocess.CompletedProcess(
                ["python-good", "-c", "probe"],
                0,
                stdout='{"importable": true, "python_version": "3.11.9"}',
                stderr="",
            ),
        }
        calls: list[str] = []

        def probe_runner(
            python: str, *, timeout: float
        ) -> subprocess.CompletedProcess[str]:
            calls.append(python)
            return probes[python]

        result = self.checker.check_install_backend_auto(
            python=None,
            timeout=1.0,
            candidates=candidates,
            probe_runner=probe_runner,
        )

        self.assertEqual(result.status, "pass")
        self.assertEqual(calls, ["/fake/python-old", "/fake/python-good"])
        self.assertIn("mode=auto", result.details)
        self.assertIn("candidates_checked=2", result.details)
        self.assertIn("selected_candidate=python-good", result.details)
        self.assertIn("python_version=3.11.9", result.details)
        self.assertEqual(self.checker.readiness_exit_code([result]), 0)

    def test_install_backend_auto_fails_with_bounded_candidate_list(self) -> None:
        candidates = tuple(
            self.checker.PythonCandidate(f"python-missing-{index}", f"/fake/{index}")
            for index in range(7)
        )

        def probe_runner(
            python: str, *, timeout: float
        ) -> subprocess.CompletedProcess[str]:
            version = "3.14." + python.rsplit("/", 1)[-1]
            return subprocess.CompletedProcess(
                [python, "-c", "probe"],
                0,
                stdout=(
                    '{"error": "ModuleNotFoundError", "importable": false, '
                    '"message": "No module named setuptools", '
                    f'"python_version": "{version}"}}'
                ),
                stderr="",
            )

        result = self.checker.check_install_backend_auto(
            python=None,
            timeout=1.0,
            candidates=candidates,
            probe_runner=probe_runner,
        )

        self.assertEqual(result.status, "fail")
        self.assertEqual(len(result.details), self.checker.MAX_DETAILS_PER_CHECK)
        self.assertIn("mode=auto", result.details)
        self.assertIn("candidates_checked=7", result.details)
        details = "\n".join(result.details)
        self.assertIn("failed_candidate=python-missing-0", details)
        self.assertIn("failed_candidate=python-missing-4", details)
        self.assertNotIn("failed_candidate=python-missing-5", details)
        self.assertIn("--install-backend-python PYTHON", details)
        self.assertIn("do not download dependencies", details)
        self.assertEqual(self.checker.readiness_exit_code([result]), 1)

    def test_install_backend_candidate_discovery_is_bounded(self) -> None:
        mapping = {
            "python3": "/fake/current",
            "python": "/fake/python",
            "python3.14": "/fake/python3.14",
            "python3.13": "/fake/python3.13",
            "python3.12": "/fake/python3.12",
            "python3.11": "/fake/python3.11",
            "python3.10": "/fake/python3.10",
            "python3.9": "/fake/python3.9",
            "python3.8": "/fake/python3.8",
        }

        candidates = self.checker.discover_install_backend_python_candidates(
            explicit_python="/fake/explicit",
            current_executable="/fake/current",
            virtual_env="/fake/venv",
            which_func=mapping.get,
        )

        labels = [candidate.label for candidate in candidates]
        self.assertLessEqual(
            len(candidates), self.checker.MAX_INSTALL_BACKEND_AUTO_CANDIDATES
        )
        self.assertEqual(labels[:3], [
            "explicit --install-backend-python",
            "current interpreter",
            "active virtualenv",
        ])
        self.assertNotIn("python3", labels)


if __name__ == "__main__":
    unittest.main()
