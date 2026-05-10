# AIOps Foundation Agent Direction

Date: 2026-05-08

## Observation

Much of real software work is operations work:

- configuration
- CI/CD
- deployment
- dependency management
- environment drift
- permission issues
- network problems
- build machine failures
- service health checks
- log inspection
- rollback decisions
- alert triage

This means Minerva's most practical early value may be in AIOps.

## Reference: BlueKing-Like Systems

BlueKing-style platforms cover:

- CMDB / asset management
- job execution
- CI/CD
- monitoring
- alerting
- standard operations workflows
- automation
- DevOps tooling

BlueKing Lite is also positioned publicly as an AI-first ops platform.

Minerva should not try to become a full BlueKing replacement.

Instead, Minerva can become:

```text
the local AI reliability agent underneath ops platforms
```

## Correct Positioning

Wrong:

```text
Minerva is a full AIOps platform.
```

Right:

```text
Minerva is a CPU-local runtime state interpreter for AIOps failures.
```

It can be embedded into:

- CI runners
- build agents
- deployment agents
- edge nodes
- observability agents
- CMDB collectors
- job execution agents
- private ops platforms

## Why Ops Is A Strong Fit

Ops problems are ideal for Minerva because they are:

- repetitive
- structured
- log-heavy
- failure-heavy
- environment-dependent
- expensive in human time
- often solvable by safe inspection
- suitable for taxonomy and action libraries

This is much easier than open-ended programming.

## AIOps Failure Classes

Minerva now keeps the first machine-readable AIOps taxonomy in
[`taxonomies/aiops-v0.json`](../taxonomies/aiops-v0.json). It covers:

### CI/CD

- dependency_install_failed
- test_failed
- lint_failed
- build_timeout
- artifact_missing
- docker_build_failed
- cache_corrupt
- runner_offline
- permission_denied
- secret_missing

### Configuration

- config_missing
- config_invalid
- env_var_missing
- wrong_endpoint
- credential_expired
- port_conflict
- path_not_found
- version_mismatch

### Deployment

- service_start_failed
- health_check_failed
- migration_failed
- image_pull_failed
- container_crash_loop
- rollback_required
- resource_limit_exceeded

### Network

- dns_failure
- tls_failure
- connection_timeout
- proxy_required
- firewall_blocked
- rate_limited

### LLM Runtime

- local_model_unavailable
- remote_model_timeout
- context_overflow
- json_schema_failure
- tool_call_failed
- unsafe_action_blocked

## AIOps Action Mapping

Small models must choose Minerva `decision.v0` actions that already exist in
the core instruction set. The AIOps taxonomy maps failure labels to read-only
diagnostics or explicit escalation:

```text
check_command_exists
check_port
check_dns
check_network
check_service_status
check_logs
inspect_file
inspect_dependencies
ask_bigger_llm
ask_user
stop
```

The runtime policy remains the safety boundary. Read-only diagnostic labels can
be allowed by default policy when confidence and risk are acceptable.
Escalation labels such as `ask_user` and `ask_bigger_llm` are intentionally
policy-blocked by default, and write-capable labels such as rollback, patching,
package installation, shell execution, or config edits are not taxonomy safe
actions.

## Minerva As A Foundation Agent

Minerva can act like a basic ops agent installed on a machine:

```text
minervad
```

Responsibilities:

- observe command failures
- read selected logs
- inspect safe config paths
- classify failures
- suggest safe actions
- decide escalation
- report structured events to a control plane

This resembles a BlueKing-style agent in deployment shape, but with a different core function:

```text
runtime interpretation and safe recovery decisioning
```

## Agent Architecture

```text
Local Node
  minervad
    Observer
    Tiny CPU LLM
    Policy Runtime
    Safe Executor
    Local Event Store
    Reporter

Control Plane
  Corpus Collector
  Eval Dashboard
  Policy Pack Manager
  Model Pack Manager
  Taxonomy Manager
```

## Deployment Modes

### Local Developer Mode

```bash
minerva observe -- npm test
```

### CI Runner Mode

```text
CI job -> Minerva -> failure decision -> annotation / next diagnostic action
```

### Ops Agent Mode

```text
minervad installed on server/edge node
```

### Platform Embedded Mode

```text
BlueKing-like platform -> Minerva API -> structured failure interpretation
```

## Why CPU-Only Matters In Ops

Ops agents often run on:

- build machines
- edge servers
- VM nodes
- low-cost instances
- internal servers without GPUs
- private network machines

Therefore Minerva's CPU sub-500M direction is not a side constraint. It is central to AIOps adoption.

## Self-Optimization In AIOps

Minerva can improve over time through evidence:

```text
failure -> decision -> action -> outcome
```

This enables:

- better failure taxonomy
- better routing rules
- better safe action mapping
- better policy defaults
- better local model distillation
- organization-specific ops knowledge

But it must not self-authorize new permissions.

## BlueKing-Like Ecosystem Opportunity

Minerva can become a small AI-native primitive for platforms like:

- CMDB
- CI/CD
- job execution
- monitoring
- alerting
- standard ops workflow

It should provide:

```text
failure interpretation as a service
```

Not:

```text
all of ops as a platform
```

## First AIOps MVP

Build:

```text
minerva observe -- <command>
```

Then support:

```text
minerva ci analyze --log build.log --junit junit.xml
minerva ops diagnose --service my-service --log app.log
```

First vertical:

```text
CI/CD failure triage
```

Why:

- high-frequency pain
- structured logs
- clear outcomes
- easy benchmark
- easy GitHub Actions integration
- strong developer adoption path

## Long-Term Vision

Minerva can become:

```text
the minimum AI ops agent for every machine
```

Chinese:

```text
每台机器上的最小 AI 运维解释 Agent
```

Its job:

```text
把配置、CI/CD、部署、网络、模型和运行时故障解释成安全、可审计、可升级的动作。
```
