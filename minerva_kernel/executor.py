from __future__ import annotations

import subprocess
import time

from .types import Observation, ProposedAction


def execute_action(action: ProposedAction, cwd: str) -> Observation:
    if action.next_action != "run_command":
        return Observation(
            command=action.next_action,
            cwd=cwd,
            exit_code=None,
            stdout_tail="",
            stderr_tail=action.reason,
            duration_ms=0,
            source="kernel",
            policy_summary="action did not execute a shell command",
        )

    command = [action.tool or "", *action.args]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    return Observation(
        command=" ".join(command),
        cwd=cwd,
        exit_code=completed.returncode,
        stdout_tail=completed.stdout[-4000:],
        stderr_tail=completed.stderr[-4000:],
        duration_ms=duration_ms,
        source="local_shell",
        policy_summary="validated before execution",
    )
