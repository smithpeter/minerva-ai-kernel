# Minerva

Minerva is a CPU-local failure interpreter for CI/CD, agents, and ops.

It keeps a minimum local reasoning path available when models, tools, networks, code, configuration, or execution environments fail.

## Positioning

```text
Minerva: CPU-local failure interpreter for CI/CD, agents, and ops.
```

Long-term category:

```text
AI Reliability Kernel
Runtime State Interpreter
```

## First Milestone

M0: Local Failure Interpreter

```bash
minerva observe -- pytest
minerva observe -- npm test
minerva observe -- docker build .
```

Expected behavior:

```text
run command
capture stdout/stderr/exit code
build observation
produce structured decision
policy-check decision
save run record
```

## Non-Negotiable Constraints

- CPU-only minimum runtime
- sub-500M model target
- no remote LLM required for minimum function
- structured output
- policy-gated execution
- read-only by default

## Core Principle

```text
LLM interprets. Policy authorizes. Executor acts.
```

## Project Docs

Start here:

- [Product strategy](docs/product-strategy.md)
- [Questions and requirements](docs/questions-and-requirements.md)
- [Execution plan and founder role](docs/execution-plan-and-founder-role.md)
- [AI team execution system](docs/ai-team-execution-system.md)
- [Most important next step](docs/most-important-next-step.md)
- [GitHub issues](docs/github-issues.md)

## Repository Status

This repository is being initialized from the Minerva research workspace. The first implementation target is `minerva observe -- <command>`.
