from __future__ import annotations

from .types import Decision, PolicyDecision


def validate_action(action: Decision) -> PolicyDecision:
    if action.escalate or action.action in {"ask_bigger_llm", "ask_user"}:
        return PolicyDecision(False, "action requested escalation")

    if action.confidence < 0.70:
        return PolicyDecision(False, "confidence below threshold")

    if action.risk != "low":
        return PolicyDecision(False, f"risk is {action.risk}")

    return PolicyDecision(True, "allowed")
