from __future__ import annotations

import json
import unittest

from minerva_kernel import Observation, redact_text
from minerva_kernel.planner import build_prompt


class RedactionTests(unittest.TestCase):
    def test_redacts_bearer_tokens(self) -> None:
        result = redact_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456")

        self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", result.value)
        self.assertIn("[REDACTED:bearer_token]", result.value)
        self.assertEqual(result.summary.to_dict(), {"count": 1, "types": ["bearer_token"]})

    def test_redacts_api_key_patterns(self) -> None:
        result = redact_text("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456")

        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", result.value)
        self.assertIn("[REDACTED:api_key]", result.value)
        self.assertEqual(result.summary.types, ("api_key",))

    def test_redacts_passwords(self) -> None:
        result = redact_text("database password: super-secret-value")

        self.assertNotIn("super-secret-value", result.value)
        self.assertIn("[REDACTED:password]", result.value)
        self.assertEqual(result.summary.types, ("password",))

    def test_redacts_private_key_blocks(self) -> None:
        private_key = (
            "-----BEGIN PRIVATE KEY-----\n"
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n"
            "-----END PRIVATE KEY-----"
        )
        result = redact_text(f"key={private_key}")

        self.assertNotIn("MIIEvQIBADANBgkqhkiG9w0BAQEFAASC", result.value)
        self.assertIn("[REDACTED:private_key]", result.value)
        self.assertEqual(result.summary.types, ("private_key",))

    def test_redacts_github_tokens(self) -> None:
        result = redact_text("token=ghp_abcdefghijklmnopqrstuvwxyzABCDEFGH12")

        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyzABCDEFGH12", result.value)
        self.assertIn("[REDACTED:github_token]", result.value)
        self.assertEqual(result.summary.types, ("github_token",))

    def test_redacts_cloud_credential_like_strings(self) -> None:
        result = redact_text("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")

        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", result.value)
        self.assertIn("[REDACTED:cloud_credential]", result.value)
        self.assertEqual(result.summary.types, ("cloud_credential",))

    def test_prompt_uses_redacted_observation_and_reports_summary(self) -> None:
        observation = Observation(
            command="curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456'",
            cwd="/workspace/minerva-ai-kernel",
            exit_code=1,
            stdout_tail="",
            stderr_tail="password=super-secret-value",
            duration_ms=120,
            source="local_shell",
            policy_summary="validated before execution",
            runtime={"api_key": "sk-abcdefghijklmnopqrstuvwxyz123456"},
        )

        prompt = build_prompt(observation)
        payload = json.loads(prompt[1]["content"].split("\n", 1)[1])

        self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", prompt[1]["content"])
        self.assertNotIn("super-secret-value", prompt[1]["content"])
        self.assertEqual(payload["redactions"]["count"], 3)
        self.assertEqual(
            payload["redactions"]["types"],
            ["bearer_token", "api_key", "password"],
        )


if __name__ == "__main__":
    unittest.main()
