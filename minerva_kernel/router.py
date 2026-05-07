from __future__ import annotations

import json
import urllib.error
import urllib.request

from .types import ProposedAction


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

    def propose(self, messages: list[dict[str, str]]) -> ProposedAction:
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
            return ProposedAction(
                diagnosis="local_llm_unavailable",
                confidence=1.0,
                next_action="ask_bigger_llm",
                tool=None,
                args=[],
                risk="low",
                escalate=True,
                reason=str(exc),
            )

        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return ProposedAction(
            diagnosis=parsed.get("diagnosis", "unknown"),
            confidence=float(parsed.get("confidence", 0.0)),
            next_action=parsed.get("next_action", "ask_bigger_llm"),
            tool=parsed.get("tool"),
            args=list(parsed.get("args", [])),
            risk=parsed.get("risk", "medium"),
            escalate=bool(parsed.get("escalate", True)),
            reason=parsed.get("reason", ""),
        )
