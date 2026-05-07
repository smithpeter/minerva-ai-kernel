# Shared Tools, Isolated State

Date: 2026-05-08

## Rule

Minerva may share tools and infrastructure with other projects, but must not share task state, project control state, or repository boundaries.

Core principle:

```text
share tools, isolate state
share infrastructure, isolate project boundaries
share dashboards, isolate task truth
```

## What May Be Shared

Allowed shared resources:

- GitHub App / GitHub CLI
- Codex / Claude / OpenClaw / Warp
- local model services such as Ollama or llama.cpp
- local OpenAI-compatible endpoints
- general AI-team workflow patterns
- Mission Control UI as a multi-project dashboard

## What Must Not Be Shared

Never share:

- `.tasks/`
- `.team/`
- run records
- project-specific state
- issue queues
- release state
- git worktrees
- configuration namespaces
- project-specific environment variables
- project-specific launch agents
- project-specific runbooks
- project-specific memory/state stores

## Repository Boundaries

Minerva root:

```text
/Users/zouyongming/projects/minerva-ai-kernel
```

Forbidden roots:

```text
/Users/zouyongming/VoxSign
/Users/zouyongming/VoxSign-decide-review
```

AI workers must stop if the git root is not the Minerva root.

## Namespaces

Minerva must use:

```text
MINERVA_*
minerva_kernel
.minerva/
~/.minerva/
```

Minerva must not use:

```text
VOXSIGN_*
voxsign
.voxsign/
~/.voxsign/
```

## Reverse Contamination Rule

VoxSign must not contaminate Minerva.

Forbidden inside Minerva:

- imports from `voxsign`
- references to `/Users/zouyongming/VoxSign` except in boundary docs/tests
- `VOXSIGN_*` environment variable usage
- `.voxsign/` or `~/.voxsign/` state usage
- VoxSign `.team/` or `.tasks/`
- VoxSign service ports as defaults
- VoxSign launch agent names
- VoxSign deploy scripts
- VoxSign-specific prompts or memory files

Allowed references:

- boundary documentation
- tests that verify VoxSign paths are forbidden
- future explicit `voxsign-integration` adapter work

## Mission Control Rule

Mission Control may display Minerva only as a separate project/workspace.

Correct:

```text
Mission Control
  Project: VoxSign
    root: /Users/zouyongming/VoxSign
    state: VoxSign-owned state

  Project: Minerva
    root: /Users/zouyongming/projects/minerva-ai-kernel
    state: Minerva-owned state
```

Incorrect:

```text
one global .team/state shared by VoxSign and Minerva
```

## AI Worker Prompt Requirement

Every Minerva AI worker prompt must include:

```text
You are working on Minerva, not VoxSign.
Before editing, confirm git root is /Users/zouyongming/projects/minerva-ai-kernel.
Do not read or modify /Users/zouyongming/VoxSign or unrelated repositories.
Use GitHub issue and .tasks card as the task source.
```

## Stop Conditions

Stop immediately if:

- git root is VoxSign
- task requires editing VoxSign
- task references VoxSign state directories
- task wants to reuse VoxSign `.team` or `.tasks`
- task needs secrets
- task wants destructive commands
- task tries to publish or deploy without explicit approval
- task imports VoxSign code into Minerva core
- task copies VoxSign-specific config into Minerva

## Enforcement

Run before agent work:

```bash
bash scripts/check-project-boundary.sh
```

Run contamination scan:

```bash
bash scripts/check-contamination.sh
```
