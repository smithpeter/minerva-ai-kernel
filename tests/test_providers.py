from __future__ import annotations

import json
import unittest
import urllib.error
from unittest.mock import patch

from minerva_kernel import Decision, MockModelProvider, check_local_provider_health
from minerva_kernel.router import LocalLLMRouter


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class _RawResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "_RawResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def read(self) -> bytes:
        return self.body


class ProviderTests(unittest.TestCase):
    def test_mock_provider_returns_deterministic_decision(self) -> None:
        provider = MockModelProvider()

        first = provider.propose([{"role": "user", "content": "diagnose failure"}])
        second = provider.propose([{"role": "user", "content": "diagnose failure"}])

        self.assertEqual(first, second)
        self.assertEqual(first.failure, "mock_provider_decision")
        self.assertEqual(first.action, "ask_user")
        self.assertEqual(len(provider.calls), 2)

    def test_router_delegates_to_injected_provider(self) -> None:
        provider = MockModelProvider(
            Decision(
                failure="configured mock",
                action="check_logs",
                confidence=0.9,
                risk="low",
                escalate=False,
                evidence=["configured evidence"],
            )
        )
        router = LocalLLMRouter(provider=provider)

        decision = router.propose([{"role": "user", "content": "anything"}])

        self.assertEqual(decision.failure, "configured mock")
        self.assertEqual(decision.action, "check_logs")
        self.assertFalse(decision.escalate)

    def test_local_router_falls_back_when_endpoint_unavailable(self) -> None:
        router = LocalLLMRouter(timeout=0.01)

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            decision = router.propose([{"role": "user", "content": "diagnose"}])

        self.assertEqual(decision.failure, "local_llm_unavailable")
        self.assertEqual(decision.action, "ask_bigger_llm")
        self.assertTrue(decision.escalate)
        self.assertEqual(decision.evidence, ["local LLM request failed"])

    def test_provider_health_reports_reachable_chat_completion_shape(self) -> None:
        response_payload = {
            "choices": [{"message": {"content": "{\"ok\": true}"}}],
        }

        with patch("urllib.request.urlopen", return_value=_FakeResponse(response_payload)):
            health = check_local_provider_health(
                base_url="http://localhost:11434/v1/chat/completions",
                model="local-test-model",
                timeout=0.1,
            )

        payload = health.to_dict()
        self.assertTrue(health.reachable)
        self.assertEqual(payload["schema_version"], "provider_health.v0")
        self.assertEqual(payload["status"], "reachable")
        self.assertEqual(payload["model"], "local-test-model")

    def test_provider_health_reports_unreachable_endpoint(self) -> None:
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            health = check_local_provider_health(timeout=0.1)

        self.assertFalse(health.reachable)
        self.assertEqual(health.status, "unreachable")
        self.assertEqual(health.detail, "URLError")

    def test_provider_health_reports_malformed_response(self) -> None:
        with patch("urllib.request.urlopen", return_value=_RawResponse(b"not json")):
            health = check_local_provider_health(timeout=0.1)

        self.assertFalse(health.reachable)
        self.assertEqual(health.status, "invalid_response")
        self.assertEqual(health.detail, "response body was not JSON")

    def test_local_router_falls_back_when_response_is_not_json(self) -> None:
        router = LocalLLMRouter()
        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": "not json",
                    }
                }
            ]
        }

        with patch("urllib.request.urlopen", return_value=_FakeResponse(response_payload)):
            decision = router.propose([{"role": "user", "content": "diagnose"}])

        self.assertEqual(decision.failure, "local_llm_invalid_response")
        self.assertEqual(decision.action, "ask_bigger_llm")
        self.assertTrue(decision.escalate)
        self.assertEqual(
            decision.evidence,
            ["local LLM response was not a valid decision"],
        )

    def test_local_router_falls_back_when_response_schema_is_invalid(self) -> None:
        router = LocalLLMRouter()
        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "failure": "missing action",
                                "confidence": 0.9,
                                "risk": "low",
                                "evidence": ["invalid fixture"],
                            }
                        ),
                    }
                }
            ]
        }

        with patch("urllib.request.urlopen", return_value=_FakeResponse(response_payload)):
            decision = router.propose([{"role": "user", "content": "diagnose"}])

        self.assertEqual(decision.failure, "local_llm_invalid_response")
        self.assertEqual(decision.action, "ask_bigger_llm")
        self.assertTrue(decision.escalate)

    def test_provider_redacts_before_and_after_local_call(self) -> None:
        token = "abcdefghijklmnopqrstuvwxyz123456"
        captured: dict[str, object] = {}
        provider_payload = {
            "failure": "auth failed",
            "action": "ask_user",
            "confidence": 0.62,
            "risk": "medium",
            "escalate": True,
            "evidence": [f"Authorization: Bearer {token}"],
            "reason": "password=super-secret-value",
        }
        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(provider_payload),
                    }
                }
            ]
        }

        def fake_urlopen(request: object, timeout: float) -> _FakeResponse:
            del timeout
            data = getattr(request, "data")
            captured["body"] = json.loads(data.decode("utf-8"))
            return _FakeResponse(response_payload)

        router = LocalLLMRouter()
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            decision = router.propose(
                [
                    {
                        "role": "user",
                        "content": f"Authorization: Bearer {token}",
                    }
                ]
            )

        body = captured["body"]
        self.assertIsInstance(body, dict)
        body_text = json.dumps(body)
        self.assertNotIn(token, body_text)
        self.assertIn("[REDACTED:bearer_token]", body_text)

        payload = decision.to_dict()
        payload_text = json.dumps(payload)
        self.assertNotIn(token, payload_text)
        self.assertNotIn("super-secret-value", payload_text)
        self.assertEqual(payload["redactions"]["count"], 2)
        self.assertEqual(payload["redactions"]["types"], ["bearer_token", "password"])


if __name__ == "__main__":
    unittest.main()
