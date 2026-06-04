# Roadmap

## M0: Local Failure Interpreter

Goal:

```text
User can run `minerva observe -- <command>`,
see an evidence-backed structured diagnosis,
and find a saved run record in `.minerva/runs/`.
```

Deliverables:

- Observation Schema v0
- Decision Schema v0
- Minerva Instruction Set v0
- `minerva diagnose failure.json`
- `minerva observe -- <command>`
- Policy Runtime v0
- Redaction v0
- 100+ failure cases
- Eval smoke test

## M1: CI/CD Failure Triage

- GitHub Actions example
- CI markdown summary
- JSON artifact output
- failure corpus contribution flow

## M2: Local Model Bench

- Qwen2.5-Coder-0.5B benchmark
- SmolLM2-360M benchmark
- SmolLM2-135M benchmark
- Minerva Failure Bench v0

## M3: Agent Tool-Call Guard

- Python SDK
- tool failure observation helper
- retry/inspect/stop/escalate decisions

## M4: Local Daemon Prototype

- `minervad`
- HTTP API
- local model health check
- audit traces

## Strategic Track: Minerva Verify

Goal:

```text
Make Minerva the local verification and reliability kernel for AI-generated
code, agent actions, CI/CD, and Linux runtime changes.
```

This track has the highest near-term success probability because AI makes code
generation cheap while verification remains the merge and deployment bottleneck.

Near-term deliverables:

- `minerva verify --diff BASE...HEAD`
- Merge Evidence Schema v0
- markdown and JSON merge evidence reports
- GitHub Action merge evidence artifact
- first 25 verification cases
- useful merge evidence rate metric

Reference:

- [Minerva Verify strategy](docs/minerva-verify-strategy.md)
- [Merge Evidence Schema v0 draft](docs/merge-evidence-schema-v0.md)
- [Minerva Verify M0 completion record](docs/minerva-verify-m0-completion.md)

## Strategic Track: Agent OS Bootstrap Layer

Goal:

```text
Define Minerva as an agent-native bootstrap and reliability layer that can run
before, beside, or underneath normal OS-level agent workloads.
```

This is a research and architecture track, not a replacement for the current
M0-M4 product proof.

Near-term deliverables:

- Agent Kernel ABI v0
- capability taxonomy v0
- audit receipt schema v0
- boot/recovery observation extensions
- QEMU-only Minerva Rescue proof plan
- Android feasibility phases that respect Verified Boot

Reference:

- [Agent OS bootstrap strategy](docs/agent-os-bootstrap-strategy.md)
- [Agent Kernel ABI v0 draft](docs/agent-kernel-abi-v0.md)
- [Future PC and Agent OS architecture watchlist](docs/future-pc-agent-architecture-watchlist.md)
