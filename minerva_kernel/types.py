from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


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
    command: str
    cwd: str
    exit_code: int | None
    stdout: str
    stderr: str
    network_status: str = "unknown"


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
