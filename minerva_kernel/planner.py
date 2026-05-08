from __future__ import annotations

import json

from .types import Observation


SYSTEM_PROMPT = """You are a local LLM scheduler controller.
Return only valid JSON.
Choose the safest next action from:
stop, retry, check_dns, check_network, check_port, inspect_file,
inspect_dependencies, search_local, check_command_exists, check_permissions,
check_service_status, check_logs, ask_bigger_llm, ask_user.
Return fields: failure, action, confidence, risk, escalate, evidence, and optional reason.
Do not propose shell commands or auto-repair.
Escalate when confidence is low, risk is medium/high, or the situation is ambiguous.
"""


def build_prompt(observation: Observation) -> list[dict[str, str]]:
    payload = observation.to_dict()
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Analyze this observation and propose one structured action:\n"
            + json.dumps(payload, ensure_ascii=True, indent=2),
        },
    ]
