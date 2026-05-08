from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from minerva_kernel import Decision, Minerva, MockModelProvider, Observation


class ToolCallError(RuntimeError):
    pass


def main() -> int:
    started = time.monotonic()
    try:
        _run_agent_tool({"query": "missing dependency failure"})
    except ToolCallError as exc:
        observation = _observation_from_tool_failure(
            tool_name="local_repo_search",
            input_keys=("query",),
            error=exc,
            duration_ms=_elapsed_ms(started),
        )
    else:
        return 0

    kernel = Minerva(
        provider=MockModelProvider(
            Decision(
                failure="agent_tool_command_missing",
                action="check_command_exists",
                confidence=0.9,
                risk="low",
                escalate=False,
                evidence=["tool error reports command not found"],
                reason="Confirm the local search command exists before retrying.",
            )
        )
    )
    diagnosis = kernel.decide(observation)

    print(
        json.dumps(
            {
                "observation": observation.to_dict(),
                "decision": diagnosis.decision.to_dict(),
                "policy_decision": {
                    "allowed": diagnosis.policy_decision.allowed,
                    "reason": diagnosis.policy_decision.reason,
                },
                "execution": {
                    "state": "not_executed",
                    "reason": (
                        "Agent adapters should treat Minerva output as advisory "
                        "unless policy allows the decision."
                    ),
                },
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if diagnosis.policy_decision.allowed else 2


def _run_agent_tool(args: dict[str, str]) -> str:
    del args
    raise ToolCallError("command not found: rg")


def _observation_from_tool_failure(
    *,
    tool_name: str,
    input_keys: tuple[str, ...],
    error: Exception,
    duration_ms: int,
) -> Observation:
    return Observation(
        command=f"agent_tool:{tool_name}",
        cwd="/workspace/example-agent",
        exit_code=None,
        stdout_tail="",
        stderr_tail=f"{error.__class__.__name__}: {error}",
        duration_ms=duration_ms,
        source="agent_tool_example",
        policy_summary=(
            "agent caught a failed local tool call; inputs are represented by "
            "key names only; Minerva must not execute recovery automatically"
        ),
        runtime={
            "agent": {
                "framework": "local_example",
                "tool_name": tool_name,
                "tool_call_id": "local-redacted-tool-call",
                "input_keys": list(input_keys),
            },
            "network_status": "not_required",
        },
    )


def _elapsed_ms(started: float) -> int:
    return max(0, int(round((time.monotonic() - started) * 1000)))


if __name__ == "__main__":
    raise SystemExit(main())
