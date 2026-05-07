# Naming Decision

Date: 2026-05-08

## Decision

Recommended name:

```text
Minerva
```

Repository/package family:

```text
minerva-ai-kernel
minerva_kernel
```

Category:

```text
AI Reliability Kernel
```

Technical subtitle:

```text
Minimum Local LLM Control Kernel
```

Chinese positioning:

```text
最小本地 LLM 可靠性内核
```

## Why Not Use `Fallback Kernel` As The Main Brand

`Fallback Kernel` is technically accurate, but it has high search noise:

- Linux kernel documentation uses the phrase heavily for firmware fallback mechanisms.
- Operating-system contexts use "fallback kernel" for boot/recovery behavior.
- It sounds like a mechanism rather than a project with long-term identity.

Use `fallback kernel` as an explanatory phrase, not as the primary brand.

## Why Not `Sentinel Kernel`

Avoid.

There is already a `sentinel-kernel` project on PyPI in the adjacent AI governance/kernel space. It positions itself as a sovereign decision trace and policy layer for autonomous systems. This creates unnecessary brand and conceptual collision.

## Why Not `Resilience Kernel`

Avoid as main brand.

It is clear but generic, and GitHub already has similarly named projects such as `Antifragile-Resilience-Kernel`. It works as a category phrase, not as a distinctive name.

## Why `Minerva`

Minerva is a strong fit because it communicates:

- wisdom
- strategy
- guarded action
- disciplined judgment
- systems-level intelligence

It avoids the crowded terms:

- agent
- OS
- router
- brain
- claw
- copilot

It can support serious infrastructure positioning:

```text
Minerva Kernel
Minerva Router
Minerva Policy
Minerva Eval
Minerva Guard
```

It also lets the project speak in precise technical language:

```text
Minerva is an AI Reliability Kernel.
It keeps a minimum local LLM online to diagnose failures, choose safe actions, and escalate when needed.
```

## Brand Architecture

Use this structure:

```text
Brand: Minerva
Repo: minerva-ai-kernel
Package: minerva_kernel
Category: AI Reliability Kernel
Subtitle: Minimum Local LLM Control Kernel
Concept phrase: fallback kernel
```

## One-Line Positioning

English:

```text
Minerva is an AI Reliability Kernel that keeps a minimum local LLM online to diagnose failures, choose safe actions, and escalate when models, tools, networks, or code fail.
```

Chinese:

```text
Minerva 是一个 AI 可靠性内核：当模型、工具、网络或代码失败时，它用最小本地 LLM 保留观察、诊断、安全动作选择和升级能力。
```

## Tagline

English:

```text
Minimum intelligence for maximum resilience.
```

Chinese:

```text
用最小智能，守住最大韧性。
```

## Naming Rules

Use:

```text
Minerva
Minerva Kernel
minerva-ai-kernel
minerva_kernel
AI Reliability Kernel
Minimum Local LLM Control Kernel
```

Avoid:

```text
Fallback Kernel as primary brand
Sentinel Kernel
Agent OS
LLM OS
AI Brain
Local Agent
```

## Practical Next Step

Create the independent project as:

```text
/Users/zouyongming/projects/minerva-ai-kernel
```

Future GitHub repository:

```text
github.com/<org-or-user>/minerva-ai-kernel
```
