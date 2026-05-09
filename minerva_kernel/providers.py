from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from .redaction import redact_value
from .types import Decision


ModelMessage = dict[str, str]


class ModelProvider(ABC):
    """Base provider interface for model-backed Decision proposals."""

    def propose(self, messages: list[ModelMessage]) -> Decision:
        redacted_messages = redact_model_messages(messages)
        return self._propose(redacted_messages).redacted()

    @abstractmethod
    def _propose(self, messages: list[ModelMessage]) -> Decision:
        raise NotImplementedError


def redact_model_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    result = redact_value(messages)
    redacted = result.value
    if not isinstance(redacted, list):
        raise ValueError("messages must be a list")

    normalized: list[ModelMessage] = []
    for message in redacted:
        if not isinstance(message, dict):
            raise ValueError("messages must contain dictionaries")
        normalized.append({str(key): str(value) for key, value in message.items()})
    return normalized


class LocalOpenAICompatibleProvider(ModelProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1/chat/completions",
        model: str = "qwen2.5-coder:0.5b-instruct",
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def _propose(self, messages: list[ModelMessage]) -> Decision:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer ollama",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            return Decision(
                confidence=1.0,
                failure="local_llm_unavailable",
                action="ask_bigger_llm",
                risk="low",
                escalate=True,
                evidence=["local LLM request failed"],
                reason=str(exc),
            )

        try:
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return Decision.from_dict(parsed)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            return Decision(
                confidence=1.0,
                failure="local_llm_invalid_response",
                action="ask_bigger_llm",
                risk="low",
                escalate=True,
                evidence=["local LLM response was not a valid decision"],
                reason=str(exc),
            )


class MockModelProvider(ModelProvider):
    """Deterministic provider for tests and CPU-only offline development."""

    def __init__(self, decision: Decision | dict[str, Any] | None = None) -> None:
        self.decision = self._coerce_decision(decision)
        self.calls: list[list[ModelMessage]] = []

    def _propose(self, messages: list[ModelMessage]) -> Decision:
        self.calls.append([dict(message) for message in messages])
        return self.decision

    @staticmethod
    def _coerce_decision(decision: Decision | dict[str, Any] | None) -> Decision:
        if decision is None:
            return Decision(
                failure="mock_provider_decision",
                action="ask_user",
                confidence=1.0,
                risk="low",
                escalate=True,
                evidence=["mock provider deterministic response"],
                reason="Mock provider returned configured offline decision.",
            )
        if isinstance(decision, Decision):
            return decision
        return Decision.from_dict(decision)
