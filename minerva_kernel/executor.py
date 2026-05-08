from __future__ import annotations

from .types import Decision, Observation


def execute_action(action: Decision, cwd: str) -> Observation:
    return Observation(
        command=action.action,
        cwd=cwd,
        exit_code=None,
        stdout_tail="",
        stderr_tail=action.reason or "",
        duration_ms=0,
        source="kernel",
        policy_summary="decision schema v0 does not execute shell commands",
    )
