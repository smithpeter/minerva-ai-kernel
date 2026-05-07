# Research Core

Date: 2026-05-08

## Final Research Direction

Minerva is not an agent framework, not an LLM gateway, and not a general coding assistant.

Minerva is:

```text
a CPU-capable AI reliability kernel powered by the smallest useful local LLM
```

Its purpose is to preserve minimum local intelligence when models, tools, networks, code, or execution environments fail.

## Core Thesis

Modern AI systems will fail in many ways:

- model unavailable
- remote API down
- network failure
- tool missing
- command error
- permission failure
- dependency failure
- malformed JSON
- context overflow
- unsafe action proposal
- repeated agent loop

The system needs a small local control layer that can still:

```text
observe -> classify -> choose safe next action -> escalate if needed
```

This local control layer should run on CPU, with no cloud dependency.

## Non-Negotiable Goal

The final runtime target should be:

```text
CPU-only
offline-capable
<= 500M parameters
GGUF deployable
structured output
policy-gated execution
```

This is the defining constraint.

If the project requires a GPU or remote LLM to perform its minimum function, it has failed its core goal.

## What The Small Model Must Do

The small model must do four things:

```text
1. classify the failure
2. choose from a small action set
3. estimate confidence/risk
4. decide whether to escalate
```

It does not need to:

- write full code patches
- perform broad reasoning
- solve unknown engineering problems
- autonomously execute arbitrary commands
- replace a stronger model

## Correct Mental Model

Wrong:

```text
small LLM as tiny autonomous engineer
```

Right:

```text
small LLM as runtime triage controller
```

Wrong:

```text
LLM decides and executes
```

Right:

```text
LLM proposes, policy validates, deterministic executor acts
```

Wrong:

```text
make a smarter agent
```

Right:

```text
make AI systems fail more safely
```

## Product Boundary

Minerva owns:

- observation schema
- failure taxonomy
- small-model routing decision
- escalation logic
- policy validation
- safe executor interface
- eval corpus
- CPU GGUF deployment

Minerva does not own:

- full IDE coding assistant experience
- long-term agent memory
- general workflow orchestration
- multi-agent collaboration
- hosted SaaS observability
- broad LLM proxy/gateway business

## Minimal Action Space

The smaller the model, the smaller the action space must be.

Initial action labels:

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
ask_bigger_llm
ask_user
```

The model should output action labels, not arbitrary commands.

The runtime maps action labels to deterministic safe operations.

## Minimal Output Schema

For sub-500M models:

```json
{
  "failure": "dns_failure",
  "action": "check_dns",
  "confidence": 0.83,
  "risk": "low",
  "escalate": false
}
```

For stronger models, richer schema is allowed, but the CPU model should stay simple.

## Failure Taxonomy Is The Core Asset

The main research artifact is not a model checkpoint.

The main research artifact is:

```text
Minerva Failure Corpus
```

It should include labeled examples for:

- shell failures
- Python tracebacks
- package manager errors
- git errors
- network/DNS/TLS failures
- port conflicts
- permission errors
- missing tools
- JSON/schema errors
- LLM provider failures
- GPU/OOM failures
- CI failures
- unsafe command proposals
- repeated-loop cases

This corpus is the basis for:

- evaluation
- distillation
- regression testing
- open-source credibility
- future model releases

## Distillation Objective

Distillation should compress behavior, not general intelligence.

Teacher models generate:

- failure label
- action label
- escalation label
- risk label
- short reason

Student models learn:

```text
observation -> compact decision object
```

Do not train long chain-of-thought into the small model.

The small model should be fast, terse, and deterministic.

## Evaluation First

The project must be evaluation-led.

Do not claim value because the model "seems smart".

Claim value only when the model improves:

- valid JSON rate
- failure classification accuracy
- safe action accuracy
- escalation recall
- dangerous action avoidance
- CPU latency
- artifact size

## North Star Metric

Use:

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
>= 80% Safe Recovery Decision Rate
>= 99% valid JSON / constrained output
>= 90% escalation recall
< 0.5% dangerous action rate
CPU median decision latency acceptable for local tools
```

## Why This Is Valuable

Most AI infrastructure optimizes for:

- smarter models
- bigger context
- more agents
- more tools
- more autonomy

Minerva optimizes for:

```text
minimum viable intelligence under failure
```

That is a different and valuable layer.

## Final Positioning

English:

```text
Minerva is a CPU-capable AI reliability kernel that keeps a minimum local LLM online to diagnose failures, choose safe actions, and escalate when models, tools, networks, or code fail.
```

Chinese:

```text
Minerva 是一个 CPU 可运行的 AI 可靠性内核：当模型、工具、网络或代码失败时，它用最小本地 LLM 保留观察、诊断、安全动作选择和升级能力。
```

## The Core Bet

The bet is:

```text
A sub-500M local model, when constrained by taxonomy, schema, policy, and deterministic execution, can provide enough intelligence to make AI systems fail safely and recover better.
```

If this is proven, Minerva becomes a foundational reliability layer for local agents, developer tools, edge devices, and private AI systems.

