from __future__ import annotations

from .types import PolicyDecision, ProposedAction


BLOCKED_TOOLS = {
    "rm",
    "sudo",
    "chmod",
    "chown",
    "mkfs",
    "dd",
    "shutdown",
    "reboot",
}


def validate_action(action: ProposedAction) -> PolicyDecision:
    if action.escalate:
        return PolicyDecision(False, "action requested escalation")

    if action.confidence < 0.70:
        return PolicyDecision(False, "confidence below threshold")

    if action.risk != "low":
        return PolicyDecision(False, f"risk is {action.risk}")

    if action.next_action == "run_command":
        if not action.tool:
            return PolicyDecision(False, "run_command requires tool")
        if action.tool in BLOCKED_TOOLS:
            return PolicyDecision(False, f"blocked tool: {action.tool}")

    return PolicyDecision(True, "allowed")
