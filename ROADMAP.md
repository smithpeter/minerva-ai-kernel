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

