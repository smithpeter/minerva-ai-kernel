# Minerva Product Strategy

Date: 2026-05-08

## Executive Summary

Minerva is a CPU-local failure interpreter for CI/CD, agents, and ops.

Its deeper mission is to make AI runtimes robust:

```text
When models, tools, networks, code, configuration, or execution environments fail,
Minerva preserves a minimum local reasoning path that can interpret the failure,
choose a safe next action, and escalate when local intelligence is insufficient.
```

Minerva should start as a narrow, useful developer/AIOps tool:

```bash
minerva observe -- pytest
minerva observe -- npm test
minerva observe -- docker build .
```

Then evolve into:

```text
a CPU-capable AI reliability kernel and runtime state interpreter
```

## Final Positioning

Practical product positioning:

```text
Minerva: CPU-local failure interpreter for CI/CD, agents, and ops.
```

Public project domain:

```text
minervakernel.com
```

Chinese:

```text
Minerva：面向 CI/CD、Agent 和运维的 CPU 本地失败解释器。
```

Technical category:

```text
AI Reliability Kernel
```

Deeper conceptual category:

```text
Runtime State Interpreter
```

Chinese:

```text
运行时状态解释器
```

## Core Thesis

Traditional interpreters translate code into machine actions.

Minerva translates runtime failure state into safe structured actions.

```text
logs + errors + exit codes + resource state + policy state
    -> failure class + safe action + risk + escalation decision
```

Chinese statement:

```text
传统编译器把代码翻译成机器指令。
Minerva 把运行时失败、日志、资源和模型状态翻译成安全行动。
```

## Original Goal: LLM Robustness

The original goal was:

```text
LLM must be robust.
Code should always be able to call an LLM.
The system should recover when models, tools, resources, or networks fail.
```

Minerva makes this concrete.

LLM robustness does not mean:

```text
one model is always correct
one model is always online
one model solves every problem
```

It means:

```text
the AI runtime always preserves a minimum local reasoning path,
can interpret failures,
can choose safe recovery actions,
and can escalate when local intelligence is insufficient.
```

## Non-Negotiable Constraints

Minerva's minimum function must be:

```text
CPU-only
offline-capable
<= 500M parameters
GGUF deployable
structured output
policy-gated execution
```

If the minimum function requires GPU or remote LLM access, the core project has failed.

## What Minerva Is

Minerva is:

- a local failure interpreter
- a tiny-model routing controller
- a policy-gated recovery advisor
- a CI/CD and AIOps triage primitive
- a data engine for failure corpus and distillation
- a reliability layer for agents and tools

## What Minerva Is Not

Minerva is not:

- a full AIOps platform
- a full agent framework
- a general chatbot
- a hosted-only observability SaaS
- a full LLM gateway
- an unrestricted auto-repair agent
- a replacement for BlueKing-like platforms

It should be embeddable under or beside those systems.

## Red-Blue Analysis

### Blue Team: Why This Matters

Most real engineering time is spent on operations-adjacent failures:

- configuration
- CI/CD
- deployment
- dependency problems
- environment drift
- permissions
- network failures
- build machine problems
- service startup failures
- model/tool failures

These problems are:

- frequent
- log-heavy
- repetitive
- expensive in human time
- suitable for safe inspection
- often solvable by known next steps

This makes them ideal for a small local model constrained by taxonomy, schema, and policy.

### Blue Team: Why CPU-Only Is Strategic

Ops agents run on:

- CI runners
- build machines
- developer laptops
- private VMs
- edge nodes
- internal servers without GPUs

Remote LLMs are often unsuitable because of:

- privacy
- cost
- latency
- network failure
- compliance
- API availability

A sub-500M CPU model is not a technical gimmick. It is the adoption requirement for this category.

### Blue Team: Why This Can Become An Ecosystem

The easiest community contribution is not code. It is failure cases.

Community can contribute:

- one CI failure
- one Python traceback
- one npm error
- one Docker failure
- one DNS/TLS failure
- one unsafe command counterexample
- one CPU benchmark

This creates a flywheel:

```text
more users -> more failure cases -> better corpus -> better distilled model -> smaller CPU model -> more users
```

### Red Team: Existing AIOps Platforms Already Exist

Concern:

```text
BlueKing, Datadog, New Relic, PagerDuty, Grafana, Splunk, Dynatrace, AI SRE tools already exist.
```

Response:

```text
Minerva is not a monitoring platform or AIOps platform.
It is a local failure interpretation layer that can be embedded into platforms.
```

Platform systems own:

- assets
- workflows
- permissions
- dashboards
- organizational processes
- job execution

Minerva owns:

- local failure evidence
- failure classification
- safe next action
- escalation decision
- structured feedback

### Red Team: Small Models May Be Too Weak

Concern:

```text
Sub-500M models cannot solve complex CI/CD or ops failures.
```

Response:

```text
They do not need to solve everything.
They need to classify common failures, choose safe next actions, and escalate correctly.
```

Correct escalation is a successful outcome.

### Red Team: Auto-Repair Is Dangerous

Concern:

```text
An LLM that repairs systems can damage systems.
```

Response:

```text
Minerva must evolve repair through levels:
diagnose -> recommend -> safe inspect -> proposed patch -> approved repair -> policy-autonomous repair
```

Default mode:

```text
read-only
no destructive commands
no credential access
no filesystem writes unless explicitly enabled
```

### Red Team: Users May Not Feel Value

Concern:

```text
If Minerva outputs vague advice, users will not return.
```

Response:

Minerva must create immediate value moments:

- extract the key error line from long logs
- name the failure precisely
- suggest a safe next action
- show evidence
- know when to escalate
- save a reusable structured record

## Product Promise

Do not promise:

```text
Minerva automatically fixes all failures.
```

Promise:

```text
Minerva finds the important failure signal, names the failure, suggests a safe next step, and escalates when unsure.
```

## First Killer Use Case

Local command/test/build failure interpretation:

```bash
minerva observe -- pytest
minerva observe -- npm test
minerva observe -- docker build .
```

First-run output:

```text
Minerva diagnosis

Failure: missing_python_dependency
Confidence: 0.88
Evidence: ModuleNotFoundError: no module named 'pytest_asyncio'
Next: inspect_dependencies
Risk: low
Escalation: not required

Saved: .minerva/runs/2026-05-08T120000Z.json
```

## Second Killer Use Case

CI/CD failure triage:

```yaml
- run: minerva observe -- npm test
```

or:

```yaml
- if: failure()
  run: minerva ci analyze --log build.log --junit junit.xml --output minerva.json
```

Outputs:

- JSON artifact
- Markdown summary
- optional PR comment
- failure label
- structured corpus record

## Third Killer Use Case

Agent tool-call failure guard:

```text
tool call failed -> Minerva decides retry / inspect / alternate tool / stop / ask bigger LLM / ask user
```

This is how Minerva becomes infrastructure for other agent systems.

## Integration Ladder

Adoption must not require deep integration first.

Use this ladder:

```text
paste/file diagnosis
-> command wrapper
-> CI wrapper
-> SDK
-> local daemon
-> platform integration
```

Each layer must provide independent value.

## Standard Observation Schema

Minimum:

```json
{
  "source": "cli",
  "command": "pytest",
  "cwd": "/repo",
  "exit_code": 1,
  "stdout_tail": "...",
  "stderr_tail": "...",
  "duration_ms": 5321
}
```

Recommended:

```json
{
  "source": "ci",
  "command": "npm test",
  "cwd": "/workspace/app",
  "exit_code": 1,
  "stdout_tail": "...",
  "stderr_tail": "...",
  "runtime": {
    "os": "linux",
    "arch": "x86_64",
    "python": "3.12.2",
    "node": "22.1.0"
  },
  "policy": {
    "mode": "read_only",
    "network": "allowed",
    "writes": "forbidden"
  }
}
```

## Minerva Instruction Set

The model should choose action labels, not arbitrary commands.

Initial instruction set:

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

The runtime maps labels to safe actions.

## Policy Runtime

Core flow:

```text
LLM proposes -> Policy validates -> Executor acts -> Feedback records
```

Principle:

```text
LLM interprets. Policy authorizes. Executor acts.
```

Chinese:

```text
LLM 解释，Policy 授权，Executor 执行。
```

## Auto-Repair Roadmap

Auto-repair must be staged.

### Level 0: Diagnose

Name the failure and show evidence.

### Level 1: Recommend

Suggest a safe next action.

### Level 2: Safe Inspect

Run read-only diagnostics.

### Level 3: Proposed Patch

Generate a patch or config change but do not apply.

### Level 4: Approved Repair

Apply reversible low-risk repair with explicit approval.

### Level 5: Policy-Autonomous Repair

Apply pre-approved low-risk repairs under strict policy.

Early Minerva should stop at Level 2 or Level 3.

## Model Strategy

Default target:

```text
<= 500M parameters
CPU GGUF
short structured output
temperature=0
constrained JSON / grammar when possible
```

Candidate models:

- Qwen2.5-Coder-0.5B-Instruct
- Qwen2.5-0.5B-Instruct
- SmolLM2-360M-Instruct
- Granite 4.0 350M
- SmolLM2-135M-Instruct for nano experiments

The small model is not a tiny autonomous engineer.

It is:

```text
classifier + router + escalator
```

## Distillation Strategy

Train behavior, not general intelligence.

Teacher output:

- failure label
- action label
- risk label
- escalation boolean
- evidence lines
- short reason

Student target:

```text
observation -> compact decision object
```

Do not train long chain-of-thought into the small model.

## Core Dataset

The main moat is:

```text
Minerva Failure Corpus
```

It should include:

- Python errors
- shell failures
- git failures
- package manager failures
- Docker failures
- CI failures
- DNS/TLS/network failures
- permission errors
- port conflicts
- model API failures
- JSON/schema failures
- unsafe command cases
- repeated-loop cases

Data must be:

- redacted
- labeled
- reviewed
- schema-valid
- safe for benchmark use

## Benchmark

Create:

```text
Minerva Failure Bench
```

Metrics:

- valid structured output rate
- failure classification accuracy
- safe action accuracy
- escalation recall
- dangerous action rate
- CPU latency
- artifact size
- user-marked helpful rate

North star:

```text
Safe Recovery Decision Rate
```

Definition:

```text
Percentage of cases where the model returns valid structured output,
classifies the failure family correctly,
chooses a safe useful action or escalates correctly,
and avoids dangerous actions.
```

Target:

```text
valid output >= 99%
safe recovery decision rate >= 80%
escalation recall >= 90%
dangerous action rate < 0.5%
```

## Technical Architecture

Research layer:

```text
Python
- datasets
- evals
- training/distillation
- reports
- prototype CLI
```

Runtime layer:

```text
Rust later
- policy engine
- safe executor
- local daemon
- audit log
- single binary
```

Inference layer:

```text
llama.cpp / Ollama
- GGUF CPU inference
- grammar constrained decoding
```

Do not build:

- LLM inference engine
- tokenizer
- GPU kernels
- training framework
- full agent framework

## Product Roadmap

### 30 Days

Deliver:

- Observation Schema v0
- Instruction Set v0
- Policy Runtime v0
- 100 hand-labeled failure cases
- `minerva observe -- <command>`
- CPU benchmarks for 3 small models

Success:

- works locally without API key
- outputs stable JSON
- no dangerous actions

### 90 Days

Deliver:

- 1,000 failure cases
- GitHub Actions integration
- Minerva Failure Bench v0
- first LoRA/QLoRA experiment for 360M/490M
- markdown/JSON CI output

Success:

- valid output >= 99%
- dangerous action rate < 0.5%
- safe recovery decision rate around 75-80%

### 180 Days

Deliver:

- 10,000+ failure cases
- `minervad` prototype
- GGUF model release
- CI/CD adapter
- CPU-only demo
- community contribution workflow

Success:

- independent developers can use Minerva for CI failure diagnosis
- project starts accumulating external failure cases

## Success Probability

Estimated by layer:

| Layer | Probability | Notes |
|---|---:|---|
| Research validation | 70% | Narrow task and sub-500M model evaluation are feasible |
| Open-source CLI success | 50% | Depends on first-run value and integration ease |
| Small model distillation success | 45% | Depends on corpus quality and schema constraints |
| AIOps product success | 25-35% | Requires trust, distribution, and platform integration |
| Ecosystem-level success | 10-20% | Requires benchmark/community flywheel |

Strategy:

```text
Win research validation first.
Then win open-source CLI.
Then expand to CI/CD and AIOps.
```

## Biggest Risks

1. Users do not feel immediate value.
2. Diagnosis is too vague.
3. Logs are not captured cleanly.
4. Privacy/security concerns block adoption.
5. Scope expands into full AIOps too early.
6. Model freely suggests unsafe commands.
7. Corpus is low quality.
8. No benchmark credibility.
9. Project relies on remote LLM for minimum function.
10. The abstract "runtime interpreter" message is used before concrete utility works.

## User Value Requirements

Minerva must create value moments:

- extract key error from long logs
- name the failure precisely
- show evidence
- suggest safe next step
- know when to escalate
- save structured record

Most important early metric:

```text
user_marked_helpful_rate
```

Architecture does not matter if this is low.

## Brand And Naming

Brand:

```text
Minerva
```

Repository:

```text
minerva-ai-kernel
```

Package:

```text
minerva_kernel
```

Tagline:

```text
Minimum intelligence for maximum resilience.
```

Chinese:

```text
用最小智能，守住最大韧性。
```

## Final Strategic Choice

Do not start with:

- full AIOps platform
- full agent framework
- autonomous repair system
- Rust-first infrastructure
- hosted SaaS

Start with:

```text
CPU-local CI/CD and command failure interpreter.
```

If that works, Minerva can grow into:

```text
the local AI reliability layer for agents, tools, CI/CD, and ops platforms.
```

## One-Sentence Strategy

```text
Minerva starts by explaining failed commands and CI jobs locally,
then becomes the CPU-only reliability layer that lets AI systems diagnose,
recover, and escalate when models, tools, networks, and runtime environments fail.
```
