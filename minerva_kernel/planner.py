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
        "command": observation.command,
        "cwd": observation.cwd,
        "exit_code": observation.exit_code,
        "stdout": observation.stdout[-4000:],
        "stderr": observation.stderr[-4000:],
        "network_status": observation.network_status,
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Analyze this observation and propose one structured action:\n"
            + json.dumps(payload, ensure_ascii=True, indent=2),
        },
    ]
