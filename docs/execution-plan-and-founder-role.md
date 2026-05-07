# Execution Plan And Founder Role

Date: 2026-05-08

## Goal

Move from strategy to execution by creating:

```text
M0: Local Failure Interpreter
```

M0 is complete when:

```text
User can run `minerva observe -- <command>`,
see an evidence-backed structured diagnosis,
and find a saved run record in `.minerva/runs/`.
```

## Operating Model

AI team handles implementation, documentation, evals, and issue creation.

Founder handles:

- strategic approval
- boundary approval
- schema approval
- high-risk decisions
- merge/release approval
- quality bar

Founder should not manually push every small step.

## Phase M0 Plan

### Workstream 1: Repository Setup

Owner:

```text
Product Agent + Docs Agent
```

Tasks:

1. Create `/Users/zouyongming/projects/minerva-ai-kernel`.
2. Initialize git.
3. Create README, ROADMAP, CONTRIBUTING, SECURITY, GOVERNANCE.
4. Create directory skeleton.
5. Add issue templates and PR template.
6. Add labels/milestones plan.

Founder does:

- approve repository path
- approve project name
- approve no-VoxSign boundary

### Workstream 2: Core Schemas

Owner:

```text
Kernel Agent + Eval Agent + Security Agent
```

Tasks:

1. Define Observation Schema v0.
2. Define Decision Schema v0.
3. Define Minerva Instruction Set v0.
4. Define Failure Taxonomy v0.
5. Define Policy Profile v0.

Founder does:

- review schema clarity
- ensure schema reflects original goal
- prevent overcomplexity

### Workstream 3: CLI MVP

Owner:

```text
Kernel Agent + Integration Agent
```

Tasks:

1. Implement `minerva diagnose failure.json`.
2. Implement `minerva observe -- <command>`.
3. Capture stdout/stderr/exit code/duration.
4. Generate observation JSON.
5. Produce structured decision.
6. Save `.minerva/runs/<run-id>.json`.

Founder does:

- test first-run UX
- confirm output feels valuable

### Workstream 4: Policy And Safety

Owner:

```text
Security Agent
```

Tasks:

1. Implement read-only default.
2. Block dangerous action labels.
3. Add redaction v0.
4. Add dangerous command test cases.
5. Add policy decision reason in output.

Founder does:

- approve safety boundary
- reject unsafe auto-repair

### Workstream 5: Failure Corpus

Owner:

```text
Eval Agent + Research Agent
```

Tasks:

1. Add 30 Python failure cases.
2. Add 30 shell/CLI failure cases.
3. Add 30 npm/node failure cases.
4. Add 30 Docker failure cases.
5. Ensure each case has expected failure/action/risk/escalation.

Founder does:

- review first 20-30 cases for quality
- add real examples from own workflows if available

### Workstream 6: Eval Harness

Owner:

```text
Eval Agent
```

Tasks:

1. Implement eval runner v0.
2. Validate structured output.
3. Measure failure label accuracy.
4. Measure action label accuracy.
5. Measure dangerous action rate.
6. Produce benchmark report.

Founder does:

- approve north-star metric
- review first benchmark result

### Workstream 7: Local Model Integration

Owner:

```text
Kernel Agent + Research Agent
```

Tasks:

1. Add provider abstraction.
2. Support mock provider first.
3. Support Ollama/OpenAI-compatible local endpoint.
4. Support llama.cpp endpoint later.
5. Benchmark Qwen2.5-Coder-0.5B.
6. Benchmark SmolLM2-360M.
7. Benchmark SmolLM2-135M.

Founder does:

- approve default model order
- confirm CPU-only requirement remains primary

### Workstream 8: CI And Release Prep

Owner:

```text
Integration Agent + Docs Agent + Growth Agent
```

Tasks:

1. Add GitHub Actions smoke test.
2. Add example CI workflow.
3. Add quickstart docs.
4. Draft launch blog post.
5. Create good-first-issues.
6. Draft failure case contribution guide.

Founder does:

- approve public messaging
- approve launch timing

## Founder Weekly Checklist

The founder should review only:

```text
1. Are we still building CPU-local failure interpretation?
2. Did this week improve first-run value?
3. Did this week improve corpus/eval?
4. Did this week preserve safety boundaries?
5. Are any agents touching VoxSign or unrelated projects?
6. What is blocked that needs human decision?
```

## Founder Daily Involvement

Target:

```text
15-30 minutes/day max
```

Founder reviews:

- PR summaries
- failed evals
- safety questions
- schema changes
- release decisions

Founder should not:

- write every issue manually
- debug every small failure
- manually push every task
- change direction daily

## AI Team Weekly Report Format

Each week, AI team reports:

```text
Progress:
- ...

Metrics:
- failure cases added:
- tests passing:
- eval smoke result:
- dangerous action failures:

User value:
- what became easier this week?

Risks:
- ...

Next issues:
- ...

Human decisions needed:
- ...
```

## Stop Conditions

Pause work if:

- repository root is VoxSign
- task needs secrets
- task wants destructive commands
- schema change breaks eval without discussion
- model suggests unsafe action and policy does not block it
- project starts drifting into full AIOps platform before M0

## Immediate Next Action

Create the independent repository:

```text
/Users/zouyongming/projects/minerva-ai-kernel
```

Then convert this plan into GitHub issues.

