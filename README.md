# Minerva

Minerva is a CPU-local failure interpreter for CI/CD, agents, and ops.

It keeps a minimum local reasoning path available when models, tools, networks, code, configuration, or execution environments fail.

Project domain:

```text
minervakernel.com
```

## Positioning

```text
Minerva: CPU-local failure interpreter for CI/CD, agents, and ops.
```

Long-term category:

```text
AI Reliability Kernel
Runtime State Interpreter
```

## Quickstart

From a local checkout:

```bash
python3 -m pip install --no-deps .
minerva doctor
minerva observe -- python3 -c "import sys; print('example failure', file=sys.stderr); sys.exit(1)"
python -m minerva_kernel.eval_smoke
```

`minerva observe --` saves a run record under `.minerva/runs/`. If no local
OpenAI-compatible provider is running, Minerva still captures the command output
and policy-blocks escalation instead of requiring a remote LLM.

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

- [M1 roadmap task seeds](docs/m1-roadmap-task-seeds.md)
- [M0 release readiness checklist](docs/m0-release-readiness.md)
- [M0 local release dry-run guide](docs/m0-local-release-dry-run.md)
- [M0 launch blog post draft](docs/m0-launch-blog-post.md)
- [M0 demo script](examples/m0-demo-script.md)
- [Product strategy](docs/product-strategy.md)
- [Questions and requirements](docs/questions-and-requirements.md)
- [Execution plan and founder role](docs/execution-plan-and-founder-role.md)
- [AI team execution system](docs/ai-team-execution-system.md)
- [Most important next step](docs/most-important-next-step.md)
- [GitHub issues](docs/github-issues.md)
- [Shared tools, isolated state](docs/shared-tools-isolated-state.md)
- [Failure case contribution guide](docs/failure-case-contributions.md)

## Repository Status

This repository is being initialized from the Minerva research workspace. The first implementation target is `minerva observe -- <command>`.

## CI Gate

Every push and pull request runs the GitHub Actions CI smoke gate. It compiles `minerva_kernel`, runs the unit test suite, and executes `python -m minerva_kernel.eval_smoke`.

## Local AI Team

Minerva has a local task board in `.tasks/` and a scoped agent loop:

```bash
bash scripts/minerva-ai-team-status.sh
bash scripts/check-project-boundary.sh
bash scripts/check-contamination.sh
bash scripts/agent-loop.sh T1
```

By default these scripts are scoped to `/Users/zouyongming/projects/minerva-ai-kernel`.
On another machine, set `MINERVA_PROJECT_ROOT` to that clone path before running the automation.
They must not be used from VoxSign.

For bounded automation, run one task tick:

```bash
bash scripts/ai-team-tick.sh
```

The tick includes an autopilot finalizer. When a worker marks a task card
`done`, the finalizer runs boundary checks, contamination checks, compile/tests,
commits, pushes, and tries to update the linked GitHub issue. A single tick can
chain multiple pending tasks until the queue is empty or
`MINERVA_AI_MAX_TASKS_PER_TICK` is reached.

To install a macOS `launchd` job that runs one tick every 30 minutes:

```bash
bash scripts/install-ai-team-launchd.sh
```

To install a Linux `systemd --user` timer that runs one tick every 30 minutes:

```bash
bash scripts/install-ai-team-systemd-user.sh
```

To stop macOS automation:

```bash
bash scripts/uninstall-ai-team-launchd.sh
```

To stop Linux automation:

```bash
bash scripts/uninstall-ai-team-systemd-user.sh
```

Check Linux timer status and logs:

```bash
systemctl --user status minerva-ai-team-tick.timer
journalctl --user -u minerva-ai-team-tick.service -n 100
```

The local loop supports Codex and Claude Code:

```bash
MINERVA_AI_EXECUTOR=codex bash scripts/ai-team-tick.sh
MINERVA_AI_EXECUTOR=claude bash scripts/ai-team-tick.sh
```

Default mode is `auto`, which prefers Codex when available.
