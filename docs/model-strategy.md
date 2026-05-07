# Model Strategy

## Goal

Find the smallest local model that can reliably perform scheduler tasks:

- classify errors
- inspect command output
- identify missing dependencies
- recognize network failures
- suggest safe next actions
- decide when to escalate

## Candidate Tiers

### L0: Tiny Local Code Controller

Recommended first model:

```text
qwen2.5-coder:0.5b-instruct
```

Why:

- small enough to keep resident
- code-specific
- useful for shell output, stack traces, and simple fixes
- available through Ollama

Example:

```bash
ollama run qwen2.5-coder:0.5b-instruct
```

### L1: Tiny General Agent Controller

Recommended model:

```text
Qwen3-0.6B-GGUF
```

Why:

- small local model
- better general reasoning than a pure code model
- supports thinking/no-thinking modes
- suitable for tool-routing experiments

### L2: Stronger Local Model

Examples:

- Qwen2.5-Coder 1.5B / 3B / 7B
- Qwen3 1.7B / 4B / 8B

Use for:

- ambiguous failures
- multi-file code analysis
- deeper planning
- risky proposed edits

### L3: Remote Strong Model

Use when:

- local confidence is low
- context is too large
- task requires stronger reasoning
- repeated local attempts fail

## Routing Rules

Start with the cheapest model that is likely to work.

Escalate when:

- confidence is below threshold
- JSON output is invalid twice
- the action fails repeatedly
- the task touches sensitive files
- the task requires nontrivial code modification
- the model says escalation is needed

## Important Constraint

The tiny model should not be treated as an autonomous engineer. It is a classifier, router, summarizer, and first-pass controller.
