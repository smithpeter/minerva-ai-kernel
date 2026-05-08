from __future__ import annotations

import json
import urllib.error
import urllib.request

from .types import Decision


class LocalLLMRouter:
    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1/chat/completions",
        model: str = "qwen2.5-coder:0.5b-instruct",
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def propose(self, messages: list[dict[str, str]]) -> Decision:
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

        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return Decision.from_dict(parsed).redacted()
