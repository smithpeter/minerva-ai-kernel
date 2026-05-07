from __future__ import annotations

import subprocess

from .types import Observation, ProposedAction


def execute_action(action: ProposedAction, cwd: str) -> Observation:
    if action.next_action != "run_command":
        return Observation(
            command=action.next_action,
            cwd=cwd,
            exit_code=None,
            stdout="",
            stderr=action.reason,
        )

    command = [action.tool or "", *action.args]
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return Observation(
        command=" ".join(command),
        cwd=cwd,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
