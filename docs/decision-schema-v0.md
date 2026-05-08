# Decision Schema v0

Decision Schema v0 is the first stable output contract for Minerva's local
failure interpreter. It lets a small model choose one bounded instruction from
Instruction Set v0 without generating arbitrary shell commands or auto-repair
steps.

## JSON Shape

```json
{
  "schema_version": "decision.v0",
  "failure": "missing_dependency",
  "action": "inspect_dependencies",
  "confidence": 0.82,
  "risk": "low",
  "escalate": false,
  "evidence": ["stderr contains ModuleNotFoundError"],
  "reason": "Dependency metadata should be inspected before retrying.",
  "redactions": {
    "count": 1,
    "types": ["password"]
  }
}
```

## Fields

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `schema_version` | yes | string | Always `decision.v0` when serialized with `Decision.to_dict()`. |
| `failure` | yes | string | Concise failure label or diagnosis. |
| `action` | yes | string | One label from Instruction Set v0. |
| `confidence` | yes | number | Float from `0.0` to `1.0`. |
| `risk` | yes | string | One of `low`, `medium`, or `high`. |
| `escalate` | yes | boolean | `true` when a larger LLM or user should handle the next step. |
| `evidence` | yes | array of strings | Non-empty observations supporting the decision. |
| `reason` | no | string | Optional short explanation for routing or audit logs. |
| `redactions` | no | object | Present when redaction changed decision text before record serialization. Contains `count` and unique `types`. |

Decision text is still redacted before serialization even though model input is
redacted first. This catches provider echoes or adapter-generated reason text
before a decision or run record is saved.

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

These labels are instructions for kernel-owned handlers. They are not a command
language, and the model must not emit shell commands, arguments, or repair
patches as part of Decision Schema v0.

## Minimal Example

```json
{
  "schema_version": "decision.v0",
  "failure": "port_in_use",
  "action": "check_port",
  "confidence": 0.9,
  "risk": "low",
  "escalate": false,
  "evidence": ["stderr contains 'address already in use'"]
}
```
