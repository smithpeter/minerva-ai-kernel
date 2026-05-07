from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ActionName = Literal[
    "stop",
    "retry",
    "run_command",
    "inspect_file",
    "search_local",
    "ask_bigger_llm",
    "ask_user",
]


@dataclass(frozen=True)
class Observation:
    """Stable Observation Schema v0 for command/runtime failures."""

    command: str
    cwd: str
    exit_code: int | None
    stdout_tail: str
    stderr_tail: str
    duration_ms: int
    source: str
    policy_summary: str
    runtime: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if not self.command:
            raise ValueError("command is required")
        if not self.cwd:
            raise ValueError("cwd is required")
        if not self.source:
            raise ValueError("source is required")
        if not self.policy_summary:
            raise ValueError("policy_summary is required")

    @property
    def stdout(self) -> str:
        return self.stdout_tail

    @property
    def stderr(self) -> str:
        return self.stderr_tail

    @property
    def network_status(self) -> str:
        value = self.runtime.get("network_status", "unknown")
        return str(value)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": "observation.v0",
            "command": self.command,
            "cwd": self.cwd,
            "exit_code": self.exit_code,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "duration_ms": self.duration_ms,
            "source": self.source,
            "policy_summary": self.policy_summary,
        }
        if self.runtime:
            payload["runtime"] = dict(self.runtime)
        return payload


@dataclass(frozen=True)
class ProposedAction:
    diagnosis: str
    confidence: float
    next_action: ActionName
    tool: str | None
    args: list[str]
    risk: Literal["low", "medium", "high"]
    escalate: bool
    reason: str


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
