from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .redaction import RedactionSummary, merge_redaction_summaries, redact_value


InstructionName = Literal[
    "stop",
    "retry",
    "check_dns",
    "check_network",
    "check_port",
    "inspect_file",
    "inspect_dependencies",
    "search_local",
    "check_command_exists",
    "check_permissions",
    "check_service_status",
    "check_logs",
    "ask_bigger_llm",
    "ask_user",
]

RiskLevel = Literal["low", "medium", "high"]

INSTRUCTION_SET_V0: tuple[InstructionName, ...] = (
    "stop",
    "retry",
    "check_dns",
    "check_network",
    "check_port",
    "inspect_file",
    "inspect_dependencies",
    "search_local",
    "check_command_exists",
    "check_permissions",
    "check_service_status",
    "check_logs",
    "ask_bigger_llm",
    "ask_user",
)

RISK_LEVELS: tuple[RiskLevel, ...] = ("low", "medium", "high")


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
    redactions: RedactionSummary | None = None

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
        return self.redacted()._to_dict()

    def _to_dict(self) -> dict[str, Any]:
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
        if self.redactions and self.redactions.count:
            payload["redactions"] = self.redactions.to_dict()
        return payload

    def redacted(self) -> "Observation":
        fields = {
            "command": self.command,
            "cwd": self.cwd,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "source": self.source,
            "policy_summary": self.policy_summary,
            "runtime": self.runtime,
        }
        redacted_fields: dict[str, Any] = {}
        summaries: list[RedactionSummary] = []
        for key, value in fields.items():
            result = redact_value(value)
            redacted_fields[key] = result.value
            summaries.append(result.summary)
        existing = [self.redactions] if self.redactions else []
        summary = merge_redaction_summaries(*(summaries + existing))
        return Observation(
            command=redacted_fields["command"],
            cwd=redacted_fields["cwd"],
            exit_code=self.exit_code,
            stdout_tail=redacted_fields["stdout_tail"],
            stderr_tail=redacted_fields["stderr_tail"],
            duration_ms=self.duration_ms,
            source=redacted_fields["source"],
            policy_summary=redacted_fields["policy_summary"],
            runtime=redacted_fields["runtime"],
            redactions=summary if summary.count else None,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Observation":
        schema_version = payload.get("schema_version")
        if schema_version != "observation.v0":
            raise ValueError(f"unsupported observation schema_version: {schema_version}")

        runtime = payload.get("runtime", {})
        if not isinstance(runtime, dict):
            raise ValueError("runtime must be an object")

        exit_code = payload.get("exit_code")
        if exit_code is not None and (
            not isinstance(exit_code, int) or isinstance(exit_code, bool)
        ):
            raise ValueError("exit_code must be an integer or null")

        duration_ms = payload.get("duration_ms")
        if not isinstance(duration_ms, int) or isinstance(duration_ms, bool):
            raise ValueError("duration_ms must be an integer")

        return cls(
            command=_required_string(payload, "command"),
            cwd=_required_string(payload, "cwd"),
            exit_code=exit_code,
            stdout_tail=_required_string(payload, "stdout_tail"),
            stderr_tail=_required_string(payload, "stderr_tail"),
            duration_ms=duration_ms,
            source=_required_string(payload, "source"),
            policy_summary=_required_string(payload, "policy_summary"),
            runtime=dict(runtime),
            redactions=_redaction_summary_from_dict(payload.get("redactions")),
        )


@dataclass(frozen=True)
class Decision:
    """Stable Decision Schema v0 returned by Minerva's interpreter."""

    failure: str
    action: InstructionName
    confidence: float
    risk: RiskLevel
    escalate: bool
    evidence: list[str] = field(default_factory=list)
    reason: str | None = None
    redactions: RedactionSummary | None = None

    def __post_init__(self) -> None:
        if not self.failure:
            raise ValueError("failure is required")
        if self.action not in INSTRUCTION_SET_V0:
            raise ValueError(f"unsupported action: {self.action}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"unsupported risk: {self.risk}")
        if not isinstance(self.escalate, bool):
            raise ValueError("escalate must be a boolean")
        if not self.evidence:
            raise ValueError("evidence is required")
        if any(not item for item in self.evidence):
            raise ValueError("evidence items must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return self.redacted()._to_dict()

    def _to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": "decision.v0",
            "failure": self.failure,
            "action": self.action,
            "confidence": self.confidence,
            "risk": self.risk,
            "escalate": self.escalate,
            "evidence": list(self.evidence),
        }
        if self.reason:
            payload["reason"] = self.reason
        if self.redactions and self.redactions.count:
            payload["redactions"] = self.redactions.to_dict()
        return payload

    def redacted(self) -> "Decision":
        fields = {
            "failure": self.failure,
            "evidence": self.evidence,
            "reason": self.reason,
        }
        redacted_fields: dict[str, Any] = {}
        summaries: list[RedactionSummary] = []
        for key, value in fields.items():
            result = redact_value(value)
            redacted_fields[key] = result.value
            summaries.append(result.summary)
        existing = [self.redactions] if self.redactions else []
        summary = merge_redaction_summaries(*(summaries + existing))
        return Decision(
            failure=redacted_fields["failure"],
            action=self.action,
            confidence=self.confidence,
            risk=self.risk,
            escalate=self.escalate,
            evidence=redacted_fields["evidence"],
            reason=redacted_fields["reason"],
            redactions=summary if summary.count else None,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Decision":
        action = payload.get("action")
        risk = payload.get("risk")
        if action not in INSTRUCTION_SET_V0:
            raise ValueError(f"unsupported action: {action}")
        if risk not in RISK_LEVELS:
            raise ValueError(f"unsupported risk: {risk}")
        escalate = payload.get("escalate", True)
        if not isinstance(escalate, bool):
            raise ValueError("escalate must be a boolean")
        evidence = payload.get("evidence", [])
        if isinstance(evidence, str) or not isinstance(evidence, list):
            raise ValueError("evidence must be a list")
        redactions = _redaction_summary_from_dict(payload.get("redactions"))
        return cls(
            failure=str(payload.get("failure", "")),
            action=action,
            confidence=float(payload.get("confidence", 0.0)),
            risk=risk,
            escalate=escalate,
            evidence=[str(item) for item in evidence],
            reason=payload.get("reason"),
            redactions=redactions,
        )


ProposedAction = Decision


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def _redaction_summary_from_dict(value: Any) -> RedactionSummary | None:
    if not isinstance(value, dict):
        return None
    count = int(value.get("count", 0))
    types = value.get("types", [])
    if isinstance(types, str) or not isinstance(types, list):
        return None
    summary = RedactionSummary(count=count, types=tuple(str(item) for item in types))
    return summary if summary.count else None


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value
