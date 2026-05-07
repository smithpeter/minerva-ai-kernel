# Red-Blue Product Positioning

Date: 2026-05-08

## Product Positioning

Recommended practical positioning:

```text
Minerva: CPU-local failure interpreter for CI/CD, agents, and ops.
```

Chinese:

```text
Minerva：面向 CI/CD、Agent 和运维的 CPU 本地失败解释器。
```

Long-term vision:

```text
AI-era runtime state interpreter.
```

Chinese:

```text
AI 时代的运行时状态解释器。
```

## Positioning Order

Use this order:

1. Local developer command failure diagnosis.
2. CI/CD failure triage.
3. Agent tool-call failure guard.
4. Ops agent installed on nodes.
5. Platform layer for BlueKing-like systems.
6. AI-era runtime state interpreter.

Do not lead with the abstract vision before the concrete use case works.

## Blue Team Case

Minerva is strong because CI/CD and ops failures are:

- frequent
- expensive
- repetitive
- log-heavy
- structured
- suitable for safe inspection
- privacy-sensitive
- often running on CPU-only machines

Minerva can turn:

```text
failure log -> structured diagnosis -> safe action -> feedback data
```

This creates a failure corpus and model improvement flywheel.

## Red Team Concerns

### Existing AIOps Platforms

BlueKing, Datadog, New Relic, PagerDuty, Grafana, Splunk, Dynatrace, and AI SRE products already exist.

Response:

```text
Minerva is not a monitoring or AIOps platform. It is a local failure interpreter that can be embedded under such platforms.
```

### Small Model Quality

Sub-500M models cannot solve complex ops failures.

Response:

```text
They do not need to solve everything. They need to classify common failures, choose safe next actions, and escalate correctly.
```

### Safety Risk

If LLMs execute commands, this becomes dangerous.

Response:

```text
The model never executes. It proposes action labels. Policy and deterministic executor control execution.
```

### Data Quality Risk

Community failure logs may be messy or sensitive.

Response:

```text
The corpus must use strict schema, redaction, label review, and policy labels.
```

## Product Phases

### Phase 1: Developer Local

```bash
minerva observe -- pytest
minerva observe -- npm test
minerva observe -- docker build .
```

### Phase 2: CI/CD

Integrations:

- GitHub Actions
- GitLab CI
- Jenkins
- BK-CI-like systems

### Phase 3: Ops Agent

```text
minervad
```

Runs on:

- build machines
- servers
- edge nodes
- internal VMs

### Phase 4: Platform Layer

Embed into:

- CMDB
- job execution
- monitoring
- CI/CD
- AIOps platforms
- agent frameworks

## Boundary

Minerva does:

- failure interpretation
- safe action recommendation
- escalation decision
- structured feedback capture

Minerva does not start by doing:

- full AIOps platform
- automatic production rollback
- automatic code modification
- unrestricted shell execution
- hosted-only observability

