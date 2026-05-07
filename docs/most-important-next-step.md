# Most Important Next Step

Date: 2026-05-08

## Decision

The most important next step is not model training, not Rust runtime, not marketing, and not platform integration.

The most important next step is:

```text
create the independent Minerva repository and implement the first measurable loop:
minerva observe -- <command>
```

## Why This Is The Most Important

All strategic claims depend on this loop:

```text
run command
capture failure evidence
build observation
call CPU local small model
produce structured decision
policy-check decision
save run record
```

Without this loop:

- no user value
- no corpus
- no eval
- no distillation data
- no AIOps integration
- no GitHub demo
- no ecosystem

## The First Proof

Command:

```bash
minerva observe -- pytest
```

Expected output:

```text
Failure: missing_python_dependency
Evidence: ModuleNotFoundError: no module named 'pytest_asyncio'
Action: inspect_dependencies
Confidence: 0.88
Risk: low
Escalation: not required
Saved: .minerva/runs/<run-id>.json
```

## Critical Path

### Step 1: Create Independent Repository

Path:

```text
/Users/zouyongming/projects/minerva-ai-kernel
```

Must not be inside VoxSign.

### Step 2: Create Skeleton

Files:

```text
README.md
ROADMAP.md
CONTRIBUTING.md
docs/
minerva_kernel/
evals/
policies/
taxonomies/
examples/
```

### Step 3: Implement Schemas

Create:

- Observation Schema v0
- Decision Schema v0
- Minerva Instruction Set v0

### Step 4: Implement CLI

Commands:

```bash
minerva diagnose failure.json
minerva observe -- <command>
```

### Step 5: Implement Policy v0

Default:

- read-only
- no destructive commands
- no credential access
- no writes

### Step 6: Implement Run Record

Save:

```text
.minerva/runs/<run-id>.json
```

### Step 7: Add First Failure Cases

Minimum:

```text
30 Python
30 shell
30 npm/node
30 Docker
```

### Step 8: Add Eval Smoke Test

Measure:

- valid output
- failure label
- action label
- dangerous action blocked

## What Not To Do Yet

Do not start with:

- training/distillation
- Rust rewrite
- daemon
- web UI
- full AIOps platform
- automatic repair
- large marketing launch
- VoxSign integration

These depend on the first loop.

## First Milestone Definition

Milestone:

```text
M0: Local Failure Interpreter
```

Done when:

```text
User can run `minerva observe -- <command>`,
see a concise evidence-backed diagnosis,
and find a saved structured run record.
```

## Founder Focus

The founder should focus on:

- approving project boundary
- approving first schemas
- reviewing first 100 failure cases
- reviewing first benchmark
- preventing scope drift

Do not spend founder time on:

- polishing architecture too early
- broad integrations
- branding refinements
- platform strategy before local value is proven

## Success Gate

M0 is successful if:

```text
first-run setup under 5 minutes
no GPU required
no API key required
diagnosis output under 10 seconds for small logs
structured decision saved locally
dangerous actions blocked by default
```

