from __future__ import annotations

import json

from .types import Observation


SYSTEM_PROMPT = """You are a local LLM scheduler controller.
Return only valid JSON.
Choose the safest next action from:
stop, retry, run_command, inspect_file, search_local, ask_bigger_llm, ask_user.
Do not propose destructive commands.
Escalate when confidence is low, risk is medium/high, or the situation is ambiguous.
"""


def build_prompt(observation: Observation) -> list[dict[str, str]]:
    payload = {
        "schema_version": "observation.v0",
        "command": observation.command,
        "cwd": observation.cwd,
        "exit_code": observation.exit_code,
        "stdout_tail": observation.stdout_tail,
        "stderr_tail": observation.stderr_tail,
        "duration_ms": observation.duration_ms,
        "source": observation.source,
        "policy_summary": observation.policy_summary,
        "runtime": observation.runtime,
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Analyze this observation and propose one structured action:\n"
            + json.dumps(payload, ensure_ascii=True, indent=2),
        },
    ]
