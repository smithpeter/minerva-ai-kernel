# Agent Tool Failure Example

This guide shows the adapter boundary for an agent tool failure. The agent
catches the failed tool call, records bounded evidence as an
`Observation`, asks Minerva for a decision, and checks policy before any
consumer handles the action.

Run the local example:

```bash
python3 examples/agent_tool_failure.py
```

The example maps the failed tool call this way:

```python
observation = Observation(
    command="agent_tool:local_repo_search",
    cwd="/workspace/example-agent",
    exit_code=None,
    stdout_tail="",
    stderr_tail="ToolCallError: command not found: rg",
    duration_ms=12,
    source="agent_tool_example",
    policy_summary=(
        "agent caught a failed local tool call; inputs are represented by "
        "key names only; Minerva must not execute recovery automatically"
    ),
    runtime={
        "agent": {
            "framework": "local_example",
            "tool_name": "local_repo_search",
            "tool_call_id": "local-redacted-tool-call",
            "input_keys": ["query"],
        },
        "network_status": "not_required",
    },
)
```

The decision is advisory. Agent adapters should read
`diagnosis.policy_decision.allowed` before routing the action to any handler,
and should not execute Minerva-proposed actions directly. The examples use
synthetic local failures, bounded log tails, redacted identifiers, and no
external service credentials.
