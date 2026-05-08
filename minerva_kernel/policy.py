from __future__ import annotations

import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .types import Decision, INSTRUCTION_SET_V0, PolicyDecision


READ_ONLY_ACTIONS = frozenset(
    {
        "stop",
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
    }
)

DANGEROUS_ACTION_LABELS = frozenset(
    {
        "apply_patch",
        "delete_file",
        "edit_file",
        "install_package",
        "modify_file",
        "repair",
        "run_command",
        "run_safe_command",
        "shell",
        "write_file",
    }
)

WRITE_TOOLS = frozenset(
    {
        "apply_patch",
        "create_file",
        "delete_file",
        "edit_file",
        "replace_file",
        "update_file",
        "write_file",
    }
)

SHELL_TOOLS = frozenset({"bash", "cmd", "powershell", "sh", "shell", "subprocess", "zsh"})

DESTRUCTIVE_COMMAND_PATTERNS = (
    "rm -rf",
    "rm -fr",
    "git reset --hard",
    "git clean -fd",
    "mkfs",
    "shutdown",
    "reboot",
)

CREDENTIAL_PATTERNS = (
    ".aws/credentials",
    ".env",
    ".git-credentials",
    ".netrc",
    "api_key",
    "authorized_keys",
    "credential",
    "id_ed25519",
    "id_rsa",
    "private_key",
    "secret",
    "token",
)


@dataclass(frozen=True)
class PolicyRuntime:
    """Deterministic policy runtime v0.

    The default posture is read-only: model payloads may only select known,
    read-oriented action labels. Shell tools, write tools, destructive commands,
    credential access, and unknown labels fail closed with explicit reasons.
    """

    read_only: bool = True

    def validate_payload(self, payload: Mapping[str, Any]) -> PolicyDecision:
        action = _string_or_none(payload.get("action"))
        tool = _string_or_none(payload.get("tool"))
        command = _string_or_none(payload.get("command"))
        target = " ".join(
            value
            for value in (
                action,
                tool,
                command,
                _string_or_none(payload.get("path")),
                _string_or_none(payload.get("args")),
            )
            if value
        )

        if _contains_credential_reference(target):
            return PolicyDecision(False, "blocked credential access attempt")

        if action in DANGEROUS_ACTION_LABELS:
            return PolicyDecision(False, f"blocked dangerous action label: {action}")

        if tool in WRITE_TOOLS:
            return PolicyDecision(False, f"blocked write-capable tool: {tool}")

        if tool in SHELL_TOOLS:
            return PolicyDecision(False, f"blocked shell tool: {tool}")

        if command and _contains_destructive_command(command):
            return PolicyDecision(False, "blocked destructive command attempt")

        if _requests_write(payload, target):
            return PolicyDecision(False, "blocked write attempt by read-only policy")

        if action is None:
            return PolicyDecision(False, "missing action label")

        if action not in INSTRUCTION_SET_V0:
            return PolicyDecision(False, f"unsupported action label: {action}")

        if self.read_only and action not in READ_ONLY_ACTIONS:
            return PolicyDecision(False, f"action is not read-only: {action}")

        if action in {"ask_bigger_llm", "ask_user"}:
            return PolicyDecision(False, "action requested escalation")

        return PolicyDecision(True, "allowed by read-only policy")

    def validate_action(self, action: Decision) -> PolicyDecision:
        payload = action.to_dict()
        decision = self.validate_payload(payload)
        if not decision.allowed:
            return decision

        if action.escalate:
            return PolicyDecision(False, "action requested escalation")

        if action.confidence < 0.70:
            return PolicyDecision(False, "confidence below threshold")

        if action.risk != "low":
            return PolicyDecision(False, f"risk is {action.risk}")

        return decision


def validate_action(action: Decision) -> PolicyDecision:
    return PolicyRuntime().validate_action(action)


def validate_payload(payload: Mapping[str, Any]) -> PolicyDecision:
    return PolicyRuntime().validate_payload(payload)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    if isinstance(value, Mapping):
        return " ".join(f"{key}={item}" for key, item in value.items())
    return str(value)


def _contains_credential_reference(value: str) -> bool:
    normalized = value.lower()
    return any(pattern in normalized for pattern in CREDENTIAL_PATTERNS)


def _contains_destructive_command(command: str) -> bool:
    try:
        normalized = " ".join(shlex.split(command.lower()))
    except ValueError:
        normalized = command.lower()
    return any(pattern in normalized for pattern in DESTRUCTIVE_COMMAND_PATTERNS)


def _requests_write(payload: Mapping[str, Any], target: str) -> bool:
    writes = payload.get("writes")
    if writes is True:
        return True
    if isinstance(writes, str) and writes.lower() not in {"", "false", "none", "no"}:
        return True

    normalized = target.lower()
    write_terms = (" write ", " create ", " delete ", " modify ", " overwrite ", " append ")
    padded = f" {normalized} "
    return any(term in padded for term in write_terms)
