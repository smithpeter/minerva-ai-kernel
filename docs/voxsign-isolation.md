# VoxSign Isolation Plan

## Goal

Fallback Kernel must be developed as an independent open-source project without modifying, depending on, or destabilizing VoxSign.

VoxSign may later become an integration target, but it must not be the development host or source of truth for this project.

## Current Boundary

Current research path:

```text
/Users/zouyongming/projects/llm-scheduler-kernel-research
```

VoxSign path:

```text
/Users/zouyongming/VoxSign
```

These are separate directories. VoxSign is a git repository. The research directory is not currently a git repository.

## Hard Rules

AI contributors must not modify:

```text
/Users/zouyongming/VoxSign
/Users/zouyongming/VoxSign-decide-review
```

unless the task explicitly says it is a VoxSign integration task.

AI contributors must only work inside:

```text
/Users/zouyongming/projects/fallback-kernel
```

or, until renamed:

```text
/Users/zouyongming/projects/llm-scheduler-kernel-research
```

## Repository Strategy

Create a new repository:

```text
fallback-kernel
```

Do not initialize it inside VoxSign.

Recommended path:

```text
/Users/zouyongming/projects/fallback-kernel
```

Future GitHub repository:

```text
github.com/<org-or-user>/fallback-kernel
```

## Namespace Rules

Python package name:

```text
fallback_kernel
```

Do not use:

```text
voxsign
openclaw
edge
center
voice
```

as package roots or internal namespace names.

Environment variable prefix:

```text
FALLBACK_KERNEL_
```

Do not use:

```text
VOXSIGN_
OPENCLAW_
```

Default ports:

```text
FK_API_PORT=8765
FK_METRICS_PORT=8766
```

Avoid VoxSign ports and service names.

## Dependency Rules

Fallback Kernel may depend on generic APIs:

- OpenAI-compatible HTTP API
- Ollama HTTP API
- llama.cpp server API
- filesystem observation interfaces
- subprocess execution under policy

Fallback Kernel must not import VoxSign modules.

Forbidden:

```python
import voxsign
from voxsign import ...
```

If VoxSign integration is needed later, it must live in a separate adapter package:

```text
integrations/voxsign_adapter/
```

or a separate repository:

```text
fallback-kernel-voxsign-adapter
```

## AI Team Work Rules

Each AI role must receive a scoped worktree/path:

| Role | Allowed Path |
|---|---|
| Research Agent | `docs/`, `research/` |
| Kernel Agent | `fallback_kernel/` |
| Eval Agent | `evals/`, `tests/` |
| Security Agent | `docs/threat-model.md`, `fallback_kernel/policy.py`, `tests/security/` |
| Docs Agent | `README.md`, `docs/`, `examples/` |
| Release Agent | `CHANGELOG.md`, release notes |

No agent may edit files outside the repository root.

## Git Rules

Before any AI-team work:

```bash
pwd
git rev-parse --show-toplevel
git status --short
```

The top-level repository must be:

```text
/Users/zouyongming/projects/fallback-kernel
```

If the top-level repository is:

```text
/Users/zouyongming/VoxSign
```

the agent must stop.

## Integration Policy

VoxSign can consume Fallback Kernel only through a stable external interface:

1. HTTP API
2. CLI
3. OpenAI-compatible endpoint
4. subprocess with JSON input/output

Avoid direct in-process imports until the kernel is stable.

Preferred first integration:

```text
VoxSign -> HTTP/CLI -> Fallback Kernel
```

Not preferred:

```text
VoxSign imports fallback_kernel internals
```

## Shared Resource Isolation

Use separate directories:

```text
~/.fallback-kernel/
~/.fallback-kernel/models/
~/.fallback-kernel/logs/
~/.fallback-kernel/evals/
```

Do not write to:

```text
~/.voxsign/
~/VoxSign/
```

unless explicitly running a VoxSign integration test.

## Safety Guard

Every AI task prompt should include:

```text
You are working on Fallback Kernel, not VoxSign.
Do not inspect or modify /Users/zouyongming/VoxSign unless explicitly instructed.
Before editing, confirm the repository root is /Users/zouyongming/projects/fallback-kernel.
```

## Recommended Next Step

Create the new project directory:

```text
/Users/zouyongming/projects/fallback-kernel
```

Then copy the research docs into it and initialize a new git repository there.

