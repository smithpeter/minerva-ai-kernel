# Branding And AI-Team Operation

## Brand Position

This project should not be positioned as another agent framework, local assistant, or generic LLM router.

It should be positioned as:

```text
AI Reliability Kernel
```

Chinese:

```text
AI 系统的可靠性内核
```

Core message:

```text
When agents, tools, networks, code, and models fail, the system still has a minimum local intelligence layer that can observe, diagnose, degrade, recover, or escalate.
```

Chinese:

```text
当 Agent、工具、网络、代码和模型失败时，系统仍然保留一个最小本地智能层，用来观察、诊断、降级、恢复或升级。
```

## Recommended Name

Earlier working name:

```text
Fallback Kernel
```

Updated recommended brand:

```text
Minerva
```

Recommended repository name:

```text
minerva-ai-kernel
```

Recommended Python package:

```text
minerva_kernel
```

Subtitle:

```text
Minimum Local LLM Control Kernel
```

Chinese name:

```text
保底智能内核
```

Category name:

```text
AI Reliability Kernel
```

## Names Considered

| Name | Strength | Weakness |
|---|---|---|
| Fallback Kernel | Clear, technical, direct | Slightly infrastructure-oriented |
| MinLLM Kernel | Emphasizes smallest local LLM | Less emotional brand value |
| Reliant | Brandable, short | Meaning less obvious |
| LastMind | Memorable | More product-like, less technical |
| KernelMind | Stable and clear | Generic |

## Recommended Tagline

English:

```text
Agents fail. Tools fail. Networks fail. Models fail. Fallback Kernel keeps a minimum local intelligence online.
```

Chinese:

```text
Agent 会失败，工具会失败，网络会失败，模型也会失败。Fallback Kernel 让系统始终保留最低限度的本地智能。
```

## Project Shape

Initial open-source layout:

```text
minerva-ai-kernel/
  README.md
  docs/
    manifesto.md
    architecture.md
    threat-model.md
    model-strategy.md
    failure-taxonomy.md
  kernel/
    router.py
    planner.py
    policy.py
    executor.py
    observer.py
  evals/
    failure-cases/
    run_eval.py
    report.md
  examples/
    shell-repair/
    python-error/
    network-failure/
  configs/
    local-qwen-0.5b.yaml
    ollama.yaml
```

## MVP

The first MVP should do only one thing:

```text
Input one failed observation, output one safe structured action.
```

Example input:

```json
{
  "command": "curl https://api.example.com",
  "exit_code": 6,
  "stderr": "Could not resolve host"
}
```

Example output:

```json
{
  "diagnosis": "dns_failure",
  "confidence": 0.91,
  "next_action": "run_safe_command",
  "tool": "dig",
  "args": ["+short", "api.example.com"],
  "risk": "low",
  "escalate": false
}
```

## Open-Source AI Team Model

The project can be run as an AI-native open-source team.

Suggested roles:

| Role | Responsibility |
|---|---|
| Founder Agent | Maintains vision, roadmap, principles |
| Research Agent | Tracks papers, competitors, related work |
| Kernel Agent | Implements router, planner, observer |
| Eval Agent | Builds failure cases and benchmark harness |
| Security Agent | Reviews policy, sandbox, dangerous actions |
| Docs Agent | Maintains README, docs, examples |
| Release Agent | Prepares changelog, issues, release notes |

## Governance Rule

AI agents may:

- create issues
- propose designs
- open pull requests
- run evals
- write risk notes
- update documentation

AI agents must not:

- directly merge to main
- change unrelated repositories
- touch secrets
- run destructive commands
- publish releases without human review
- modify VoxSign-owned files unless explicitly assigned

Human review remains required for:

- merge to main
- release publishing
- security policy changes
- filesystem permission expansion
- network or credential integrations
- changes that affect another project

## First Week Plan

1. Rename or copy this research into `minerva-ai-kernel`.
2. Write `manifesto.md`.
3. Write `failure-taxonomy.md`.
4. Prepare 30 failure cases.
5. Run first local eval using `qwen2.5-coder:0.5b-instruct`.
6. Publish README.
7. Open initial GitHub issues:

```text
good first issue
eval
policy
router
docs
security
```
