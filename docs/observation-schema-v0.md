# Observation Schema v0

Observation Schema v0 is the first stable input contract for Minerva's local
failure interpreter. It captures the result of a command or runtime action
without storing full logs or adding inference-specific fields.

## JSON Shape

```json
{
  "schema_version": "observation.v0",
  "command": "pytest tests/test_cli.py",
  "cwd": "/workspace/project",
  "exit_code": 1,
  "stdout_tail": "... last relevant stdout bytes ...",
  "stderr_tail": "... last relevant stderr bytes ...",
  "duration_ms": 842,
  "source": "local_shell",
  "policy_summary": "validated before execution",
  "runtime": {
    "python": "3.14.0",
    "platform": "darwin",
    "network_status": "unknown"
  },
  "redactions": {
    "count": 2,
    "types": ["bearer_token", "password"]
  }
}
```

## Fields

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `schema_version` | yes | string | Always `observation.v0` when serialized with `Observation.to_dict()`. |
| `command` | yes | string | Command, tool invocation, or action name that produced the observation. |
| `cwd` | yes | string | Working directory where the command or action ran. |
| `exit_code` | yes | integer or null | Process exit status, or `null` when no process was run. |
| `stdout_tail` | yes | string | Bounded stdout tail. Full logs should stay outside the observation. |
| `stderr_tail` | yes | string | Bounded stderr tail. Full logs should stay outside the observation. |
| `duration_ms` | yes | integer | Non-negative elapsed time in milliseconds. |
| `source` | yes | string | Producer identifier such as `local_shell`, `kernel`, `manual`, or an adapter name. |
| `policy_summary` | yes | string | Short policy/runtime safety summary attached before interpretation. |
| `runtime` | no | object | Optional metadata about interpreter, OS, package manager, network, CI job, or adapter context. |
| `redactions` | no | object | Present when redaction changed the observation before model input or record serialization. Contains `count` and unique `types`. |

## Default Collection

Observation Schema v0 is designed for compact runtime evidence, not bulk data
capture. By default Minerva records the command or tool label, working
directory, exit code, bounded stdout and stderr tails, duration, source, policy
summary, and optional non-secret runtime metadata such as interpreter version,
platform, package manager, CI provider, or network status.

Minerva does not collect full logs, full environment variables, `.env` files,
credential files, browser cookies, SSH keys, private keys, tokens, passwords,
cloud credentials, or secret values by default. If an adapter includes optional
logs or metadata, those strings must be redacted before model input and before
the saved observation or run record is written.

## Redaction Metadata

The v0 redactor targets obvious bearer tokens, API key patterns, passwords,
private key blocks, GitHub tokens, and cloud credential-like strings. It is a
basic safety layer, not a full DLP system. When it redacts content, the
serialized observation includes a summary:

```json
{
  "redactions": {
    "count": 3,
    "types": ["bearer_token", "api_key", "password"]
  }
}
```

## Minimal Example

```json
{
  "schema_version": "observation.v0",
  "command": "python3 -m compileall minerva_kernel",
  "cwd": "/workspace/minerva-ai-kernel",
  "exit_code": 0,
  "stdout_tail": "Listing 'minerva_kernel'...",
  "stderr_tail": "",
  "duration_ms": 120,
  "source": "local_shell",
  "policy_summary": "validated before execution"
}
```

## Recommended Example

```json
{
  "schema_version": "observation.v0",
  "command": "pytest tests/test_cli.py",
  "cwd": "/workspace/minerva-ai-kernel",
  "exit_code": 1,
  "stdout_tail": "",
  "stderr_tail": "ModuleNotFoundError: No module named 'minerva_kernel'",
  "duration_ms": 931,
  "source": "local_shell",
  "policy_summary": "non-destructive command; full logs omitted",
  "runtime": {
    "python": "3.14.0",
    "platform": "darwin",
    "network_status": "unknown"
  }
}
```
