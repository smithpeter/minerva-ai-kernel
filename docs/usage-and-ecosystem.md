# Usage And Ecosystem Strategy

Date: 2026-05-08

## Core Usage Principle

Minerva should be easy to adopt without replacing an existing stack.

It should sit underneath or beside existing tools:

```text
Application / Agent / Script / CI / Edge Device
        |
        v
Minerva Reliability Kernel
        |
        v
Safe action / escalation / local diagnosis
```

The adoption path must be incremental.

## Primary Users

### 1. Local Developers

Use case:

```text
my command failed; classify the failure and suggest a safe next step
```

Integration:

```bash
minerva observe -- npm test
minerva diagnose failure.json
minerva doctor
```

Value:

- works offline
- runs on CPU
- helps diagnose local environment issues
- does not require sending logs to cloud models

### 2. Agent Framework Authors

Use case:

```text
agent tool call failed; ask Minerva whether to retry, inspect, escalate, or stop
```

Integration:

```python
from minerva_kernel import Minerva

decision = Minerva().decide(observation)
```

Value:

- safer tool failure handling
- reduced runaway loops
- local fallback when cloud LLM fails
- structured escalation logic

### 3. LLM Gateways And Routers

Use case:

```text
model request failed; route to local CPU model or escalate
```

Integration:

```text
LiteLLM / Portkey / custom gateway -> Minerva decision endpoint
```

Value:

- failure-aware model routing
- local fallback policy
- outage diagnosis

### 4. CI/CD Systems

Use case:

```text
test failed; classify cause and propose safe next diagnostic action
```

Integration:

```bash
minerva ci --input junit.xml --stderr build.log --json
```

Value:

- fast triage
- failure clustering
- safe suggestions
- offline private repo support

### 5. Edge Devices

Use case:

```text
device has no GPU and unreliable network; still needs basic AI failure triage
```

Integration:

```text
Minerva GGUF + llama.cpp + local policy file
```

Value:

- CPU-only
- small artifact
- no cloud dependency
- field diagnostics

### 6. Enterprise Private AI Teams

Use case:

```text
AI systems must not fail silently or execute unsafe recovery actions
```

Integration:

```text
Minerva as policy-gated reliability layer
```

Value:

- audit-friendly decisions
- local inference
- no log exfiltration
- safer autonomous systems

## Adoption Interfaces

Minerva should expose four interfaces.

### CLI

For developers and CI:

```bash
minerva diagnose failure.json
minerva observe -- python script.py
minerva eval run evals/failure-cases
minerva doctor
```

### Python SDK

For frameworks:

```python
from minerva_kernel import Minerva, Observation

kernel = Minerva()
decision = kernel.decide(Observation(...))
```

### HTTP API

For language-agnostic systems:

```text
POST /v1/decide
POST /v1/diagnose
GET /health
```

### OpenAI-Compatible Mode

Optional compatibility layer:

```text
/v1/chat/completions
```

But this should not be the main interface. Minerva's native interface is structured decisioning, not chat.

## Extension Points

### Failure Taxonomy Packs

Community can contribute domain packs:

```text
python
node
rust
go
docker
kubernetes
git
network
llm-provider
gpu
ci
embedded
```

Each pack includes:

- examples
- labels
- safe actions
- test cases
- policy notes

### Policy Packs

Examples:

```text
read-only
local-dev
ci-safe
enterprise-strict
edge-offline
human-approval
```

### Model Packs

Examples:

```text
minerva-qwen-coder-500m
minerva-smollm2-360m
minerva-smollm2-135m
```

### Adapters

Adapters should be separate and optional:

```text
minerva-langgraph
minerva-autogen
minerva-crewai
minerva-litellm
minerva-ollama
minerva-llamacpp
minerva-vscode
minerva-github-actions
```

Avoid coupling Minerva core to any framework.

## Ecosystem Structure

Recommended repository structure:

```text
minerva-ai-kernel/
  minerva_kernel/
  evals/
  docs/
  examples/
  adapters/
  policies/
  taxonomies/
  models/
```

Possible future split:

```text
minerva-ai-kernel          # core runtime
minerva-failure-corpus     # dataset and benchmark
minerva-models             # model cards and release scripts
minerva-adapters           # framework adapters
minerva-policies           # policy packs
```

Do not split too early. Start monorepo until project structure stabilizes.

## First Killer Use Case

The first killer use case should be:

```text
Local command/test failure triage on CPU
```

Why:

- easy to demo
- easy to evaluate
- no cloud dependency
- directly useful to developers
- produces real failure data
- does not require deep integration

Demo:

```bash
minerva observe -- pytest
```

Output:

```json
{
  "failure": "missing_dependency",
  "action": "inspect_dependencies",
  "confidence": 0.86,
  "risk": "low",
  "escalate": false
}
```

## Second Killer Use Case

Agent tool-call failure guard:

```text
When an agent tool fails, Minerva decides retry / inspect / alternate tool / stop / escalate.
```

This is where Minerva becomes infrastructure for other agents.

## Community Contribution Model

The easiest contribution should be adding failure cases.

Contribution types:

```text
failure case
taxonomy label
safe action mapping
policy rule
adapter
model eval result
documentation
```

Good first issues:

- add 10 Python traceback cases
- add 10 npm failure cases
- add DNS/TLS failure examples
- add dangerous command test cases
- add CPU benchmark result
- add llama.cpp example

## Model Ecosystem

Minerva should not depend on one model.

It should benchmark and publish a leaderboard:

```text
Minerva Failure Bench
```

Columns:

- model
- parameters
- GGUF size
- CPU latency
- valid JSON rate
- safe recovery decision rate
- escalation recall
- dangerous action rate

This creates an ecosystem where small models compete on reliability, not chat quality.

## Ecosystem Flywheel

The flywheel:

```text
more users -> more real failure cases -> better corpus -> better distilled model -> smaller CPU model -> more adoption
```

The project should optimize for this loop.

## What To Avoid

Avoid:

- becoming a general chatbot
- becoming a full agent framework
- becoming a hosted-only SaaS
- requiring GPU for core use
- relying on remote LLM for minimum function
- accepting arbitrary shell command generation
- coupling core to VoxSign or any one product
- overclaiming autonomy

## Ecosystem Message

English:

```text
Bring your agent, tool, script, or CI system. Minerva gives it a CPU-local reliability layer for failures.
```

Chinese:

```text
保留你的 Agent、工具、脚本或 CI 系统。Minerva 给它们增加一个 CPU 本地可运行的失败可靠性层。
```

