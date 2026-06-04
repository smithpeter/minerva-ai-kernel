from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from minerva_kernel.cli import main as cli_main
from minerva_kernel.verify import (
    DiffEntry,
    SafeCheck,
    SafeCheckResult,
    apply_verification_checks,
    build_merge_evidence_from_entries,
    render_merge_evidence_markdown_from_file,
    render_merge_evidence_json,
    render_merge_evidence_markdown,
)


class VerifyTests(unittest.TestCase):
    def test_docs_and_planning_diff_produces_caution_report(self) -> None:
        report = build_merge_evidence_from_entries(
            [
                DiffEntry(status="M", path="README.md"),
                DiffEntry(status="A", path="docs/minerva-verify-strategy.md"),
                DiffEntry(status="A", path=".tasks/T59.task.md"),
            ],
            diff_spec="origin/main...HEAD",
            repository="minerva-ai-kernel",
            created_at="2026-06-04T00:00:00Z",
        )

        self.assertEqual(report["schema_version"], "merge_evidence.v0")
        self.assertEqual(report["summary"]["risk_level"], "low")
        self.assertEqual(report["summary"]["merge_readiness"], "caution")
        self.assertEqual(report["summary"]["changed_files"], 3)
        self.assertEqual(report["summary"]["primary_areas"], ["docs", "planning"])
        self.assertEqual(report["policy"]["decision"], "allowed")
        self.assertTrue(report["policy"]["writes_detected"])
        self.assertIn("unit_tests", {item["kind"] for item in report["unverified"]})
        self.assertIn(
            "review docs for roadmap/schema consistency",
            report["recommended_next_steps"],
        )

    def test_runtime_diff_recommends_compile_and_eval_smoke(self) -> None:
        report = build_merge_evidence_from_entries(
            [DiffEntry(status="M", path="minerva_kernel/cli.py")],
            diff_spec="main...feature",
            repository="minerva-ai-kernel",
            created_at="2026-06-04T00:00:00Z",
        )

        self.assertEqual(report["summary"]["risk_level"], "medium")
        self.assertEqual(report["summary"]["merge_readiness"], "caution")
        self.assertEqual(report["summary"]["primary_areas"], ["runtime"])
        self.assertIn(
            "python3 -m compileall minerva_kernel",
            report["recommended_next_steps"],
        )
        self.assertIn(
            "python3 -m minerva_kernel.eval_smoke",
            report["recommended_next_steps"],
        )

    def test_dangerous_added_command_blocks_report(self) -> None:
        report = build_merge_evidence_from_entries(
            [DiffEntry(status="M", path="scripts/deploy.sh")],
            diff_spec="main...feature",
            repository="minerva-ai-kernel",
            created_at="2026-06-04T00:00:00Z",
            added_lines=["rm -rf /tmp/example"],
        )

        self.assertEqual(report["summary"]["risk_level"], "high")
        self.assertEqual(report["summary"]["merge_readiness"], "blocked")
        self.assertTrue(report["policy"]["dangerous_actions_detected"])
        self.assertEqual(report["policy"]["decision"], "blocked")
        self.assertEqual(report["recommended_next_steps"][0], "resolve blocked policy signals before running further verification")

    def test_json_and_markdown_render_contract(self) -> None:
        report = build_merge_evidence_from_entries(
            [DiffEntry(status="M", path="pyproject.toml")],
            diff_spec="main...feature",
            repository="minerva-ai-kernel",
            created_at="2026-06-04T00:00:00Z",
        )

        payload = json.loads(render_merge_evidence_json(report))
        markdown = render_merge_evidence_markdown(report)

        self.assertEqual(payload["schema_version"], "merge_evidence.v0")
        self.assertEqual(payload["subject"]["base"], "main")
        self.assertEqual(payload["subject"]["head"], "feature")
        self.assertIn("dependencies", payload["summary"]["primary_areas"])
        self.assertIn("# Minerva Merge Evidence", markdown)
        self.assertIn("Merge readiness: `caution`", markdown)
        self.assertIn("`dependency_change`", markdown)

    def test_cli_verify_diff_outputs_json_from_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _git(repo, "init")
            _git(repo, "config", "user.email", "minerva@example.invalid")
            _git(repo, "config", "user.name", "Minerva Test")
            (repo / "README.md").write_text("# Example\n", encoding="utf-8")
            _git(repo, "add", "README.md")
            _git(repo, "commit", "-m", "initial")
            (repo / "README.md").write_text("# Example\n\nUpdate docs.\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                cli_main(["verify", "--diff", "HEAD", "--format", "json", "--cwd", tmpdir])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], "merge_evidence.v0")
        self.assertEqual(payload["summary"]["changed_files"], 1)
        self.assertEqual(payload["changed_files"][0]["path"], "README.md")
        self.assertEqual(payload["summary"]["risk_level"], "low")

    def test_cli_verify_can_include_untracked_files_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _git(repo, "init")
            _git(repo, "config", "user.email", "minerva@example.invalid")
            _git(repo, "config", "user.name", "Minerva Test")
            (repo / "README.md").write_text("# Example\n", encoding="utf-8")
            _git(repo, "add", "README.md")
            _git(repo, "commit", "-m", "initial")
            (repo / "docs").mkdir()
            (repo / "docs" / "new.md").write_text("# New\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                cli_main(
                    [
                        "verify",
                        "--diff",
                        "HEAD",
                        "--format",
                        "json",
                        "--cwd",
                        tmpdir,
                        "--include-untracked",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["summary"]["changed_files"], 1)
        self.assertEqual(payload["changed_files"][0]["status"], "?")
        self.assertEqual(payload["changed_files"][0]["path"], "docs/new.md")

    def test_cli_verify_can_write_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _git(repo, "init")
            _git(repo, "config", "user.email", "minerva@example.invalid")
            _git(repo, "config", "user.name", "Minerva Test")
            (repo / "README.md").write_text("# Example\n", encoding="utf-8")
            _git(repo, "add", "README.md")
            _git(repo, "commit", "-m", "initial")
            (repo / "README.md").write_text("# Example\n\nUpdate docs.\n", encoding="utf-8")
            output_path = repo / "out" / "merge-evidence.json"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                cli_main(
                    [
                        "verify",
                        "--diff",
                        "HEAD",
                        "--format",
                        "json",
                        "--cwd",
                        tmpdir,
                        "--output",
                        str(output_path),
                    ]
                )

            self.assertEqual(stdout.getvalue(), "")
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "merge_evidence.v0")
            self.assertEqual(payload["changed_files"][0]["path"], "README.md")

    def test_cli_verify_can_exclude_unrelated_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _git(repo, "init")
            _git(repo, "config", "user.email", "minerva@example.invalid")
            _git(repo, "config", "user.name", "Minerva Test")
            (repo / "README.md").write_text("# Example\n", encoding="utf-8")
            (repo / "notes.txt").write_text("safe\n", encoding="utf-8")
            _git(repo, "add", "README.md", "notes.txt")
            _git(repo, "commit", "-m", "initial")
            (repo / "README.md").write_text("# Example\n\nUpdate docs.\n", encoding="utf-8")
            (repo / "notes.txt").write_text("token = should_be_ignored\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                cli_main(
                    [
                        "verify",
                        "--diff",
                        "HEAD",
                        "--format",
                        "json",
                        "--cwd",
                        tmpdir,
                        "--exclude",
                        "notes.txt",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["summary"]["changed_files"], 1)
        self.assertEqual(payload["changed_files"][0]["path"], "README.md")
        self.assertEqual(payload["policy"]["decision"], "allowed")

    def test_cli_verify_treats_docs_tests_and_evals_as_example_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _git(repo, "init")
            _git(repo, "config", "user.email", "minerva@example.invalid")
            _git(repo, "config", "user.name", "Minerva Test")
            (repo / "README.md").write_text("# Example\n", encoding="utf-8")
            _git(repo, "add", "README.md")
            _git(repo, "commit", "-m", "initial")
            (repo / "docs").mkdir()
            (repo / "evals").mkdir()
            (repo / "tests").mkdir()
            (repo / "docs" / "agent.md").write_text(
                "The model must not inspect secrets or run secret_read.\n",
                encoding="utf-8",
            )
            (repo / "evals" / "verify_cases_v0.json").write_text(
                '{"added_lines":["rm -rf /tmp/minerva",'
                '"openai_api_key=sk-abcdefghijklmnopqrstuvwxyz"]}\n',
                encoding="utf-8",
            )
            (repo / "tests" / "test_verify.py").write_text(
                'example = "token = should_be_ignored"\n',
                encoding="utf-8",
            )
            _git(
                repo,
                "add",
                "docs/agent.md",
                "evals/verify_cases_v0.json",
                "tests/test_verify.py",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                cli_main(["verify", "--diff", "HEAD", "--format", "json", "--cwd", tmpdir])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["summary"]["changed_files"], 3)
        self.assertEqual(payload["policy"]["decision"], "allowed")
        self.assertFalse(payload["policy"]["dangerous_actions_detected"])
        self.assertFalse(payload["policy"]["secret_access_detected"])

    def test_cli_verify_still_blocks_runtime_secret_and_destructive_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _git(repo, "init")
            _git(repo, "config", "user.email", "minerva@example.invalid")
            _git(repo, "config", "user.name", "Minerva Test")
            (repo / "minerva_kernel").mkdir()
            (repo / "minerva_kernel" / "app.py").write_text("SAFE = True\n", encoding="utf-8")
            _git(repo, "add", "minerva_kernel/app.py")
            _git(repo, "commit", "-m", "initial")
            (repo / "minerva_kernel" / "app.py").write_text(
                'OPENAI_API_KEY = "sk-abcdefghijklmnopqrstuvwxyz"\n'
                'command = "rm -rf /tmp/minerva"\n',
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                cli_main(["verify", "--diff", "HEAD", "--format", "json", "--cwd", tmpdir])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["summary"]["merge_readiness"], "blocked")
        self.assertEqual(payload["policy"]["decision"], "blocked")
        self.assertTrue(payload["policy"]["dangerous_actions_detected"])
        self.assertTrue(payload["policy"]["secret_access_detected"])

    def test_render_merge_evidence_markdown_from_file(self) -> None:
        report = build_merge_evidence_from_entries(
            [DiffEntry(status="M", path="README.md")],
            diff_spec="main...feature",
            repository="minerva-ai-kernel",
            created_at="2026-06-04T00:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "merge-evidence.json"
            path.write_text(render_merge_evidence_json(report), encoding="utf-8")

            markdown = render_merge_evidence_markdown_from_file(path)

        self.assertIn("# Minerva Merge Evidence", markdown)
        self.assertIn("Changed files: `1`", markdown)

    def test_apply_verification_checks_promotes_ready_when_evidence_covers_risk(self) -> None:
        report = build_merge_evidence_from_entries(
            [DiffEntry(status="M", path="minerva_kernel/verify.py")],
            diff_spec="main...feature",
            repository="minerva-ai-kernel",
            created_at="2026-06-04T00:00:00Z",
        )
        seen: list[str] = []

        def fake_runner(check: SafeCheck, _repo: Path) -> SafeCheckResult:
            seen.append(check.kind)
            return SafeCheckResult(
                kind=check.kind,
                command=check.command,
                exit_code=0,
                stdout_tail="ok",
                stderr_tail="",
            )

        updated = apply_verification_checks(report, check_runner=fake_runner)

        self.assertEqual(
            seen,
            ["compile", "unit_tests", "verify_eval", "runtime_smoke"],
        )
        self.assertEqual(updated["summary"]["merge_readiness"], "ready")
        self.assertFalse(updated["unverified"])
        verified_status = {
            item["kind"]: item["status"]
            for item in updated["verified"]
            if "status" in item
        }
        self.assertEqual(verified_status["compile"], "passed")
        self.assertEqual(verified_status["unit_tests"], "passed")
        self.assertEqual(verified_status["verify_eval"], "passed")
        self.assertEqual(verified_status["runtime_smoke"], "passed")

    def test_apply_verification_checks_blocks_when_allowlisted_check_fails(self) -> None:
        report = build_merge_evidence_from_entries(
            [DiffEntry(status="M", path="tests/test_verify.py")],
            diff_spec="main...feature",
            repository="minerva-ai-kernel",
            created_at="2026-06-04T00:00:00Z",
        )

        def fake_runner(check: SafeCheck, _repo: Path) -> SafeCheckResult:
            exit_code = 1 if check.kind == "unit_tests" else 0
            return SafeCheckResult(
                kind=check.kind,
                command=check.command,
                exit_code=exit_code,
                stdout_tail="",
                stderr_tail="failed" if exit_code else "",
            )

        updated = apply_verification_checks(report, check_runner=fake_runner)

        self.assertEqual(updated["summary"]["merge_readiness"], "blocked")
        self.assertEqual(updated["summary"]["risk_level"], "high")
        self.assertIn(
            "verification_check_failed",
            {risk["id"] for risk in updated["risks"]},
        )
        unit_result = next(
            item for item in updated["verified"] if item["kind"] == "unit_tests"
        )
        self.assertEqual(unit_result["status"], "failed")
        self.assertEqual(unit_result["exit_code"], 1)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
