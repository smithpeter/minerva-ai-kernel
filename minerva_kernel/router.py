from __future__ import annotations

from .providers import LocalOpenAICompatibleProvider, ModelMessage, ModelProvider
from .types import Decision


class LocalLLMRouter:
    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1/chat/completions",
        model: str = "qwen2.5-coder:0.5b-instruct",
        timeout: float = 20.0,
        provider: ModelProvider | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.provider = provider or LocalOpenAICompatibleProvider(
            base_url=base_url,
            model=model,
            timeout=timeout,
        )

    def propose(self, messages: list[ModelMessage]) -> Decision:
        return self.provider.propose(messages)
