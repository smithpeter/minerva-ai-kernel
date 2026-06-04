# Agent Kernel ABI v0

Date: 2026-06-04

Status: draft

## Purpose

This document defines the first draft of Minerva's Agent Kernel ABI.

The ABI is the stable contract between:

- agent frameworks
- local tools
- installers and recovery environments
- operating-system services
- `minervad`
- policy packs
- model packs
- audit stores

The goal is to make Minerva usable as a lower-level reliability and
authorization layer without forcing every integrator to adopt Minerva's CLI.

## Core Rule

```text
Agent intent is probabilistic.
Minerva authorization is deterministic.
```

Models may propose decisions. They must not directly receive ambient authority
to execute commands, write files, inspect secrets, modify boot state, or install
an OS.

## ABI Calls

```text
observe(event) -> observation
decide(observation, context) -> decision
authorize(decision, capabilities) -> policy_decision
execute(decision, authorization) -> execution_observation
audit(record) -> audit_receipt
escalate(record, target) -> escalation_receipt
```

## Object Model

### Agent Event

Input from a caller, tool wrapper, installer, daemon, or recovery environment.

```json
{
  "schema_version": "agent_event.v0",
  "source": "ci_runner",
  "event_type": "command_failed",
  "cwd": "/repo",
  "command": "pytest",
  "exit_code": 1,
  "stdout_tail": "",
  "stderr_tail": "ModuleNotFoundError: No module named 'pytest_asyncio'",
  "runtime": {
    "os": "linux",
    "arch": "x86_64",
    "network_status": "unknown"
  }
}
```

### Observation

Normalized Minerva evidence. This maps to the current `Observation` schema and
adds room for boot/recovery evidence.

```json
{
  "schema_version": "observation.v0",
  "command": "pytest",
  "cwd": "/repo",
  "exit_code": 1,
  "stdout_tail": "",
  "stderr_tail": "ModuleNotFoundError: No module named 'pytest_asyncio'",
  "duration_ms": 1200,
  "source": "ci_runner",
  "policy_summary": "read-only default; bounded logs",
  "runtime": {
    "os": "linux",
    "arch": "x86_64",
    "network_status": "unknown"
  }
}
```

### Decision

The model or deterministic baseline returns a small structured decision.

```json
{
  "schema_version": "decision.v0",
  "failure": "missing_dependency",
  "action": "inspect_dependencies",
  "confidence": 0.89,
  "risk": "low",
  "escalate": false,
  "evidence": ["stderr contains ModuleNotFoundError"],
  "reason": "Dependency metadata should be inspected before retrying."
}
```

### Capability Request

The decision is mapped to requested capabilities before execution.

```json
{
  "schema_version": "capability_request.v0",
  "action": "inspect_dependencies",
  "capabilities": [
    {
      "name": "filesystem.read",
      "scope": "/repo",
      "writes": false
    }
  ],
  "risk": "low"
}
```

### Policy Decision

Policy must fail closed.

```json
{
  "schema_version": "policy_decision.v0",
  "allowed": true,
  "reason": "allowed by read-only policy",
  "granted_capabilities": [
    {
      "name": "filesystem.read",
      "scope": "/repo",
      "expires_after_ms": 30000
    }
  ]
}
```

### Execution Observation

Execution returns another observation, not an opaque side effect.

```json
{
  "schema_version": "observation.v0",
  "command": "executor:inspect_dependencies",
  "cwd": "/repo",
  "exit_code": 0,
  "stdout_tail": "dependency metadata files:\n- found: pyproject.toml",
  "stderr_tail": "",
  "duration_ms": 12,
  "source": "kernel_executor",
  "policy_summary": "explicit read-only executor; no shell commands or writes",
  "runtime": {
    "policy_allowed": true,
    "executor_state": "completed"
  }
}
```

### Audit Receipt

Audit records are append-only receipts for later review and corpus generation.

```json
{
  "schema_version": "audit_receipt.v0",
  "record_id": "run_20260604_000001",
  "created_at": "2026-06-04T00:00:00Z",
  "hash": "sha256:...",
  "previous_hash": "sha256:...",
  "redactions": {
    "count": 0,
    "types": []
  }
}
```

## Capability Taxonomy v0

### Filesystem

```text
filesystem.read
filesystem.write
filesystem.search
filesystem.metadata
filesystem.secret_read
```

Default:

```text
read/search/metadata may be allowed in scoped roots
write and secret_read are denied
```

### Process

```text
process.inspect
process.exec
process.kill
process.retry
```

Default:

```text
inspect may be allowed
exec/kill/retry require explicit policy profile
```

### Network

```text
network.dns
network.tcp_probe
network.http_get
network.http_write
network.proxy_inspect
```

Default:

```text
dns/tcp/http_get may be allowed by profile
http_write denied unless approved
```

### Boot And Installer

```text
boot.inspect
boot.modify
firmware.inspect
firmware.modify
partition.inspect
partition.modify
os.install
os.repair
recovery.install
```

Default:

```text
inspect only
modify/install/repair denied outside a reviewed bootstrap profile
```

### Agent Runtime

```text
agent.tool_call
agent.memory_read
agent.memory_write
agent.model_route
agent.escalate
agent.stop
```

Default:

```text
model_route/escalate/stop may be allowed
memory_write and tool_call require scoped grants
```

## Boot And Recovery Observation Extensions

Bootstrap environments need fields that normal CI does not.

```json
{
  "schema_version": "observation.v0",
  "source": "minerva_bootstrap",
  "runtime": {
    "boot_phase": "live_installer",
    "firmware_type": "uefi",
    "secure_boot": "enabled",
    "verified_boot": "not_applicable",
    "bootloader": "systemd-boot",
    "target_os": "linux",
    "storage": {
      "disk_count": 1,
      "has_free_space": true,
      "partition_table": "gpt"
    },
    "network": {
      "interfaces": 1,
      "dns_status": "unknown"
    },
    "installer_step": "preflight"
  }
}
```

## Policy Invariants

- Redact before model input.
- Unknown actions are denied.
- Unknown capabilities are denied.
- Secret reads are denied by default.
- Writes are denied by default.
- Boot, firmware, partition, and OS install actions require explicit profile.
- Model-provided shell commands are never executed directly.
- Every authorized action must produce an audit record.
- Escalation is a valid successful outcome.

## Current Code Mapping

| ABI concept | Current implementation |
| --- | --- |
| Observation | `minerva_kernel.types.Observation` |
| Decision | `minerva_kernel.types.Decision` |
| Policy decision | `minerva_kernel.types.PolicyDecision` |
| Policy runtime | `minerva_kernel.policy.PolicyRuntime` |
| Read-only executor | `minerva_kernel.executor.execute_action` |
| Run record | `.minerva/runs/*.json` |
| Local daemon seed | `minerva minervad` |

## Versioning

ABI versions should be explicit:

```text
agent_event.v0
observation.v0
decision.v0
capability_request.v0
policy_decision.v0
audit_receipt.v0
```

Breaking changes require a new schema version.

## First Implementation Tasks

1. Add `capability_request.v0`.
2. Add `audit_receipt.v0`.
3. Extend observation runtime fixtures with boot/recovery fields.
4. Add docs-only examples for CI, local daemon, x86 bootstrap, and Android ADB.
5. Add tests that deny boot/partition/write capabilities by default.

