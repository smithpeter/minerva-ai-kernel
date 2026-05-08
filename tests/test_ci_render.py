from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from minerva_kernel.ci_render import (
    CI_ARTIFACT_SCHEMA_VERSION,
    MARKDOWN_EXCERPT_CHARS,
    build_ci_artifact,
    render_markdown_summary,
)
from minerva_kernel.cli import main


_ARTIFACT_TOP_LEVEL_FIELDS = {
    "schema_version",
    "created_at",
    "ci",
    "summary",
    "run_record",
    "safety",
}
_SUMMARY_FIELDS = {
    "status",
    "observed_exit_code",
    "failure",
    "action",
    "confidence",
    "risk",
    "escalate",
    "policy_allowed",
    "policy_reason",
    "redaction_count",
    "redaction_types",
}
_SAFETY_FIELDS = {
    "auto_repair",
    "model_input_redacted",
    "artifact_redacted",
    "policy_gated",
    "github_api_credentials_required",
    "notes",
}


class CiRenderTests(unittest.TestCase):
    def test_artifact_happy_path_is_deterministic_and_credential_free(self) -> None:
        record = _run_record()
        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_WORKFLOW": "ci",
            "GITHUB_JOB": "test",
            "GITHUB_RUN_ID": "1234567890",
            "GITHUB_RUN_ATTEMPT": "2",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/17/merge",
            "GITHUB_SHA": "abc123",
            "GITHUB_TOKEN": "ghp_should_not_be_rendered_1234567890",
        }

        artifact = build_ci_artifact(record, env=env)
        repeated = build_ci_artifact(record, env=env)

        self.assertEqual(artifact, repeated)
        self.assertEqual(artifact["schema_version"], "minerva_ci_run.v0")
        self.assertEqual(artifact["created_at"], "2026-05-08T12:00:00Z")
        self.assertEqual(
            artifact["ci"],
            {
                "provider": "github_actions",
                "workflow": "ci",
                "job": "test",
                "run_id": "1234567890",
                "attempt": 2,
                "event_name": "pull_request",
                "ref": "refs/pull/17/merge",
                "sha": "abc123",
            },
        )
        self.assertEqual(artifact["summary"]["status"], "failed_policy_allowed")
        self.assertTrue(artifact["summary"]["policy_allowed"])
        self.assertFalse(artifact["safety"]["auto_repair"])
        self.assertNotIn("GITHUB_TOKEN", json.dumps(artifact))
        self.assertNotIn("ghp_should_not_be_rendered", json.dumps(artifact))

    def test_artifact_contract_fields_for_regression_cases(self) -> None:
        token = "abcdefghijklmnopqrstuvwxyz123456"
        cases = (
            (
                "happy_path",
                _run_record(),
                {
                    "status": "failed_policy_allowed",
                    "policy_allowed": True,
                    "policy_reason": "allowed by read-only policy",
                    "redaction_count": 0,
                    "redaction_types": [],
                },
            ),
            (
                "policy_blocked",
                _run_record(
                    action="ask_bigger_llm",
                    risk="low",
                    policy_allowed=False,
                    policy_reason="action is not read-only: ask_bigger_llm",
                ),
                {
                    "status": "blocked_by_policy",
                    "policy_allowed": False,
                    "policy_reason": "action is not read-only: ask_bigger_llm",
                    "redaction_count": 0,
                    "redaction_types": [],
                },
            ),
            (
                "redaction",
                _run_record(
                    stdout_tail=f"Authorization: Bearer {token}\n",
                    evidence=[f"stdout included Bearer {token}"],
                ),
                {
                    "status": "failed_policy_allowed",
                    "policy_allowed": True,
                    "policy_reason": "allowed by read-only policy",
                    "redaction_count": 2,
                    "redaction_types": ["bearer_token"],
                },
            ),
        )

        for name, record, expected_summary in cases:
            with self.subTest(name=name):
                artifact = build_ci_artifact(record, env={})

                self.assertEqual(set(artifact), _ARTIFACT_TOP_LEVEL_FIELDS)
                self.assertEqual(
                    artifact["schema_version"],
                    CI_ARTIFACT_SCHEMA_VERSION,
                )
                self.assertEqual(artifact["created_at"], "2026-05-08T12:00:00Z")
                self.assertEqual(set(artifact["summary"]), _SUMMARY_FIELDS)
                self.assertEqual(set(artifact["safety"]), _SAFETY_FIELDS)
                self.assertEqual(
                    artifact["run_record"]["schema_version"],
                    "run.v0",
                )
                self.assertEqual(
                    {key: artifact["summary"][key] for key in expected_summary},
                    expected_summary,
                )
                self.assertFalse(artifact["safety"]["auto_repair"])
                self.assertTrue(artifact["safety"]["model_input_redacted"])
                self.assertTrue(artifact["safety"]["artifact_redacted"])
                self.assertTrue(artifact["safety"]["policy_gated"])
                self.assertFalse(artifact["safety"]["github_api_credentials_required"])

    def test_policy_blocked_path_is_policy_aware(self) -> None:
        record = _run_record(
            action="ask_bigger_llm",
            risk="low",
            policy_allowed=False,
            policy_reason="action is not read-only: ask_bigger_llm",
        )

        artifact = build_ci_artifact(record, env={})
        markdown = render_markdown_summary(record, run_record_path=".minerva/runs/run.json")

        self.assertEqual(artifact["summary"]["status"], "blocked_by_policy")
        self.assertFalse(artifact["summary"]["policy_allowed"])
        self.assertEqual(
            artifact["summary"]["policy_reason"],
            "action is not read-only: ask_bigger_llm",
        )
        self.assertIn("Status: blocked by policy", markdown)
        self.assertIn("policy blocked the decision", markdown)
        self.assertIn("`action is not read-only: ask_bigger_llm`", markdown)

    def test_redaction_propagates_to_markdown_and_artifact(self) -> None:
        token = "abcdefghijklmnopqrstuvwxyz123456"
        record = _run_record(
            stdout_tail=f"Authorization: Bearer {token}\n",
            evidence=[f"stdout included Bearer {token}"],
        )

        artifact = build_ci_artifact(record, env={})
        markdown = render_markdown_summary(record)
        artifact_text = json.dumps(artifact)

        self.assertNotIn(token, artifact_text)
        self.assertNotIn(token, markdown)
        self.assertIn("[REDACTED:bearer_token]", artifact_text)
        self.assertIn("[REDACTED:bearer_token]", markdown)
        self.assertEqual(artifact["summary"]["redaction_count"], 2)
        self.assertEqual(artifact["summary"]["redaction_types"], ["bearer_token"])
        self.assertEqual(
            artifact["run_record"]["redactions"],
            {"count": 2, "types": ["bearer_token"]},
        )
        self.assertIn("count=2 types=bearer_token", markdown)

    def test_markdown_summary_is_bounded_and_credential_free(self) -> None:
        bearer_token = "abcdefghijklmnopqrstuvwxyz123456"
        github_token = "ghp_" + ("A" * 24)
        api_key = "sk-" + ("B" * 24)
        cloud_credential = "AKIA" + ("C" * 16)
        password = "correcthorsebatterystaple"
        stdout_tail = (
            ("safe stdout line\n" * 180)
            + f"Authorization: Bearer {bearer_token}\n"
            + f"{github_token}\n"
            + f"openai_api_key={api_key}\n"
            + f"{cloud_credential}\n"
            + f"password={password}\n"
            + ("safe trailing stdout line\n" * 6)
        )
        stderr_tail = (
            ("safe stderr line\n" * 150)
            + f"Authorization: Bearer {bearer_token}\n"
            + ("safe trailing stderr line\n" * 6)
        )
        record = _run_record(
            stdout_tail=stdout_tail,
            stderr_tail=stderr_tail,
            evidence=[
                f"saw token {github_token}",
                f"saw api key {api_key}",
                f"saw cloud key {cloud_credential}",
            ],
        )

        markdown = render_markdown_summary(record)

        self.assertLessEqual(len(markdown), (2 * MARKDOWN_EXCERPT_CHARS) + 2200)
        self.assertEqual(
            markdown.count(f"[truncated to last {MARKDOWN_EXCERPT_CHARS} chars]"),
            2,
        )
        for secret in (
            bearer_token,
            github_token,
            api_key,
            cloud_credential,
            password,
        ):
            self.assertNotIn(secret, markdown)
        self.assertNotRegex(markdown, r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b")
        self.assertNotRegex(markdown, r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")
        self.assertNotRegex(markdown, r"\bsk-[A-Za-z0-9]{20,}\b")
        self.assertNotRegex(markdown, r"\bAKIA[A-Z0-9]{16}\b")
        self.assertIn("[REDACTED:bearer_token]", markdown)
        self.assertIn("[REDACTED:github_token]", markdown)
        self.assertIn("[REDACTED:api_key]", markdown)
        self.assertIn("[REDACTED:cloud_credential]", markdown)
        self.assertIn("[REDACTED:password]", markdown)

    def test_cli_render_commands_read_run_record_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = Path(tmpdir) / "run.json"
            run_path.write_text(json.dumps(_run_record()), encoding="utf-8")

            summary_stdout = io.StringIO()
            with contextlib.redirect_stdout(summary_stdout):
                main(["render-ci-summary", str(run_path)])

            artifact_stdout = io.StringIO()
            with contextlib.redirect_stdout(artifact_stdout):
                main(
                    [
                        "render-ci-artifact",
                        "--created-at",
                        "2026-05-08T12:30:00Z",
                        str(run_path),
                    ]
                )

        self.assertIn("# Minerva CI Summary", summary_stdout.getvalue())
        artifact = json.loads(artifact_stdout.getvalue())
        self.assertEqual(artifact["schema_version"], "minerva_ci_run.v0")
        self.assertEqual(artifact["created_at"], "2026-05-08T12:30:00Z")


def _run_record(
    *,
    action: str = "inspect_dependencies",
    risk: str = "low",
    policy_allowed: bool = True,
    policy_reason: str = "allowed by read-only policy",
    stdout_tail: str = "Using bounded stdout\n",
    stderr_tail: str = "ModuleNotFoundError: No module named 'minerva_kernel'\n",
    evidence: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "run.v0",
        "created_at": "2026-05-08T12:00:00Z",
        "observation": {
            "schema_version": "observation.v0",
            "command": "python3 -m unittest discover -s tests",
            "cwd": "/workspace/minerva-ai-kernel",
            "exit_code": 1,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "duration_ms": 931,
            "source": "local_shell",
            "policy_summary": (
                "command attempted with 20s timeout; "
                "stdout/stderr tails limited to 12000 chars"
            ),
            "runtime": {
                "python": "3.14.0",
                "platform": "linux",
                "network_status": "unknown",
                "timeout_seconds": 20.0,
                "tail_chars": 12000,
                "stdout_truncated": False,
                "stderr_truncated": False,
                "timed_out": False,
                "command_found": True,
            },
        },
        "decision": {
            "schema_version": "decision.v0",
            "failure": "missing_dependency",
            "action": action,
            "confidence": 0.82,
            "risk": risk,
            "escalate": False,
            "evidence": evidence or ["stderr contains ModuleNotFoundError"],
        },
        "policy_decision": {
            "allowed": policy_allowed,
            "reason": policy_reason,
        },
    }


if __name__ == "__main__":
    unittest.main()
