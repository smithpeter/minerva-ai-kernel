# Scheduler Loop

## Loop

```text
1. Observe
2. Summarize
3. Ask LLM
4. Parse JSON
5. Validate policy
6. Dispatch bounded instruction
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

## Decision Schema

The LLM must return JSON:

```json
{
  "failure": "dns_failure",
  "action": "check_dns",
  "confidence": 0.86,
  "risk": "low",
  "escalate": false,
  "evidence": ["stderr contains 'Could not resolve host'"],
  "reason": "The command failed before connecting, so DNS should be checked first."
}
```

## Instruction Set v0

```text
stop
retry
check_dns
check_network
check_port
inspect_file
inspect_dependencies
search_local
check_command_exists
check_permissions
check_service_status
check_logs
ask_bigger_llm
ask_user
```

## Policy Examples

Reject:

- arbitrary shell command generation
- credential access
- filesystem writes outside allowed roots
- network access when disabled
- low-confidence decisions

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
