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
- [Shared tools, isolated state](docs/shared-tools-isolated-state.md)

## Repository Status

This repository is being initialized from the Minerva research workspace. The first implementation target is `minerva observe -- <command>`.

## Local AI Team

Minerva has a local task board in `.tasks/` and a scoped agent loop:

```bash
bash scripts/minerva-ai-team-status.sh
bash scripts/check-project-boundary.sh
bash scripts/check-contamination.sh
bash scripts/agent-loop.sh T1
```

These scripts are scoped to `/Users/zouyongming/projects/minerva-ai-kernel` and must not be used from VoxSign.

For bounded automation, run one task tick:

```bash
bash scripts/ai-team-tick.sh
```

To install a macOS launchd job that runs one tick every 30 minutes:

```bash
bash scripts/install-ai-team-launchd.sh
```

To stop it:

```bash
bash scripts/uninstall-ai-team-launchd.sh
```
