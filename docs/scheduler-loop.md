# Scheduler Loop

## Loop

```text
1. Observe
2. Summarize
3. Ask LLM
4. Parse JSON
5. Validate policy
6. Execute
7. Record outcome
8. Repeat or stop
```

## Observation

Minimum observation object:

```json
{
  "command": "curl -sS https://example.com",
  "cwd": "/repo",
  "exit_code": 6,
  "stdout": "",
  "stderr": "Could not resolve host: example.com",
  "network_status": "unknown"
}
```

## Action Schema

The LLM must return JSON:

```json
{
  "diagnosis": "dns_failure",
  "confidence": 0.86,
  "next_action": "run_command",
  "tool": "dig",
  "args": ["+short", "example.com"],
  "risk": "low",
  "escalate": false,
  "reason": "The command failed before connecting, so DNS should be checked first."
}
```

## Allowed Actions

```text
stop
retry
run_command
inspect_file
search_local
ask_bigger_llm
ask_user
```

## Policy Examples

Reject:

- destructive commands
- credential access
- filesystem writes outside allowed roots
- network access when disabled
- low-confidence command execution

Escalate:

- repeated failure
- invalid JSON
- ambiguous diagnosis
- command requires elevated permission
- action has medium or high risk

## Success Criteria

The scheduler is useful if it can reliably handle:

- missing command
- missing dependency
- syntax error
- failing test
- port already in use
- DNS failure
- HTTP timeout
- permission denied
- model endpoint unavailable
