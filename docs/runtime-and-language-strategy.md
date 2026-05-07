# Runtime And Language Strategy

Date: 2026-05-08

## Decision

Do not begin with low-level binary/system implementation.

Begin with:

```text
Python research runtime + llama.cpp/Ollama backend + eval harness
```

Then evolve toward:

```text
Rust runtime daemon + single-binary CLI + GGUF CPU model
```

## Why Python First

The first research risk is not system language performance.

The first research risk is whether this is true:

```text
A sub-500M CPU model can reliably classify failures, choose safe actions, and escalate under strict constraints.
```

Python is best for proving this because it has mature tooling for:

- eval harnesses
- datasets
- JSON schemas
- model calls
- PEFT/QLoRA
- synthetic data generation
- reports
- fast iteration

## What Should Stay Python

Keep these in Python at first:

- research experiments
- failure corpus tooling
- eval runner
- model comparison
- distillation data generation
- training scripts
- notebooks/reports
- prototype CLI

## What Should Become Rust Later

Rust is the best long-term choice for security-critical local runtime pieces:

- policy engine
- executor sandbox
- audit log writer
- local daemon
- capability checks
- filesystem boundary enforcement
- timeout/resource control
- JSON schema validation for decisions
- stable CLI binary

## What Should Not Be Built From Scratch

Do not build:

- LLM inference engine
- tokenizer
- GPU kernels
- training framework
- model format
- full agent framework

Use:

- llama.cpp for GGUF CPU inference
- Ollama for local dev convenience
- Transformers/PEFT/Unsloth/LLaMA-Factory for training
- JSON schema / grammar constrained decoding when available

## Runtime Phases

### Phase 1: Research Runtime

Language:

```text
Python
```

Purpose:

- prove the model-task fit
- define schema
- build evals
- test sub-500M models
- generate teacher data

Deliverables:

- `minerva diagnose`
- `minerva observe -- <command>`
- eval harness
- failure corpus

### Phase 2: Local Service Runtime

Language:

```text
Python or Rust prototype
```

Purpose:

- expose stable local API
- support CPU GGUF inference
- manage model health
- support local policy packs

Deliverables:

- `minervad`
- `POST /v1/decide`
- `/health`
- local config
- audit trace

### Phase 3: Rust Reliability Runtime

Language:

```text
Rust
```

Purpose:

- make the core reliable, embeddable, auditable, and easy to deploy

Deliverables:

- single binary `minerva`
- daemon `minervad`
- `libminerva`
- deterministic policy engine
- safe executor

### Phase 4: Embedded / Edge Runtime

Language:

```text
Rust + C ABI / WASM optional
```

Purpose:

- make Minerva usable in edge devices, CI runners, enterprise desktops, local agents, and private deployments

Deliverables:

- CPU-only model bundle
- static binary
- policy packs
- minimal dependencies

## Recommended Architecture

```text
Python Research Layer
  - datasets
  - evals
  - distillation
  - reports

Rust Runtime Layer
  - policy
  - executor
  - daemon
  - audit
  - API

llama.cpp Layer
  - GGUF inference
  - CPU execution
  - grammar constrained decoding
```

## Go vs Rust

Use Rust when:

- enforcing policy
- executing commands
- managing filesystem boundaries
- producing a single local binary
- exposing FFI
- targeting edge/embedded devices

Use Go only if:

- the project needs a simple cloud-native gateway
- HTTP service ergonomics matter more than local safety boundaries
- a separate control-plane service is created

Default long-term core language:

```text
Rust
```

## Binary Distribution Goal

Long-term distribution should be:

```text
minerva binary
minervad binary
GGUF model file
policy pack
taxonomy pack
```

Example:

```text
minerva-ai-kernel/
  bin/minerva
  bin/minervad
  models/minerva-micro-360m-q4.gguf
  policies/local-dev.yaml
  taxonomies/python.yaml
```

## Engineering Guardrail

Do not let low-level implementation replace the research core.

The proof remains:

```text
Can a CPU sub-500M model safely route failures under constraints?
```

Only move a component to Rust when:

- the schema is stable
- the eval proves value
- policy boundaries are clear
- Python prototype is too fragile for deployment

