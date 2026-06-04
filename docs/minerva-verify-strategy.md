# Minerva Verify Strategy

Date: 2026-06-04

## Decision

Minerva's highest-probability strategic path is:

```text
AI-era local verification and reliability kernel.
```

The first product should be:

```text
Minerva Verify: merge evidence for AI-generated code, agent actions, CI, and
Linux runtime changes.
```

This is more urgent and more achievable than starting with a new operating
system or firmware layer. The OS/bootstrap strategy remains important, but it
should sit underneath a stronger core thesis:

```text
AI generates candidates.
Minerva generates trust.
```

## Why Verification Is The Right Center

AI makes code generation cheap. It does not make correctness cheap.

The bottleneck moves from:

```text
Can we write a patch?
```

to:

```text
Can we trust this patch enough to merge, deploy, or let an agent act?
```

In practice, the hard questions are:

- What changed?
- What is affected?
- What evidence exists?
- What remains unverified?
- What can break after merge?
- What should a human reviewer focus on?
- Which tests, traces, logs, or runtime checks are missing?
- Can the decision be reproduced later?

Minerva should make these questions machine-readable, repeatable, and auditable.

## Core Product Thesis

```text
Minerva is not a better coding agent.
Minerva is the verification layer every coding agent should pass through.
```

Models can propose code, tests, summaries, and risk hypotheses. Minerva should
own the evidence contract:

```text
diff -> impact -> verification plan -> execution evidence -> residual risk -> merge evidence
```

## Red Team

### Attack: Verification Is Impossible In General

Many changes have no complete oracle. Tests can pass while behavior, security,
performance, or user experience regresses.

Response:

```text
Minerva should not claim full correctness.
It should separate verified evidence from unverified risk.
```

### Attack: Reports Become Noise

If every PR gets a long AI report, human reviewers will ignore it.

Response:

```text
The report must be evidence-first, short, structured, and focused on merge risk.
```

### Attack: Models Hallucinate Confidence

LLMs can make unsupported claims and hide uncertainty.

Response:

```text
Confidence must be tied to artifacts, commands, tests, logs, schemas, and
explicit unknowns.
```

### Attack: Existing CI Already Verifies Code

GitHub Actions, test suites, linters, type checkers, and coverage tools already
exist.

Response:

```text
CI produces raw signals.
Minerva interprets whether the signals are sufficient for the change.
```

### Attack: Generalizing Across Repos Is Too Hard

Every repository has different languages, conventions, risk areas, and release
rules.

Response:

```text
Start with narrow repo-local profiles and learn from repeated evidence records.
```

### Attack: Human Review Remains The Bottleneck

Even better reports might not remove the need for human judgment.

Response:

```text
The goal is not to remove humans.
The goal is to turn human review from code archaeology into evidence review.
```

## Blue Team

### Why This Can Work

Verification has natural structure:

- diffs
- files
- tests
- commands
- logs
- dependencies
- schemas
- coverage
- policy gates
- historical failures
- post-merge outcomes

That structure is ideal for Minerva because Minerva already has:

- observations
- decisions
- policy gates
- redaction
- bounded execution
- run records
- CI artifacts
- failure corpus
- eval reports

### Why Linux And GitHub Are The Best Starting Point

Linux and GitHub are the easiest proving ground because:

- repositories are observable
- diffs are explicit
- tests and CI are common
- logs are available
- actions are scriptable
- evidence can be stored as artifacts
- failure cases can be collected
- open-source projects provide real data

This creates the fastest feedback loop.

## The Real Moat

The moat is not the model.

The moat is:

```text
real engineering changes
verification plans
execution evidence
human review outcomes
merge decisions
post-merge regressions
failure fixes
```

Over time this becomes a verification corpus:

```text
change -> evidence -> decision -> outcome
```

That corpus can train, evaluate, and improve verification agents.

## M0 Product

M0 should be a local CLI and GitHub Action:

```bash
minerva verify --diff origin/main...HEAD --format markdown
minerva verify --diff origin/main...HEAD --run --format markdown
minerva verify --diff origin/main...HEAD --run --format json --output minerva-merge-evidence.json
```

### M0 Input

- git diff
- changed files
- dependency file changes
- test command results
- CI logs
- Minerva run records
- optional repository profile

### M0 Output

```text
Merge Evidence Report
```

The report answers:

- What changed?
- What areas are affected?
- What evidence was collected?
- What remains unverified?
- What is the merge risk?
- What is the next best verification step?
- Is the PR merge-ready, caution, or blocked?

### M0 Non-Goals

- no auto-merge
- no unrestricted code edits
- no claim of formal correctness
- no broad OS integration
- no firmware or boot changes
- no mandatory remote LLM

## Merge Readiness Levels

```text
ready
caution
blocked
unknown
```

Definitions:

- `ready`: evidence covers the main risk areas for this change.
- `caution`: key checks passed, but important risk remains unverified.
- `blocked`: evidence shows a failure, policy violation, or missing required check.
- `unknown`: Minerva cannot classify the change with enough evidence.

## Immediate Work

The next implementation task should be:

```text
T58: Define Minerva Verify M0 and Merge Evidence Schema v0
```

Then:

```text
T59: Implement `minerva verify --diff` as a docs/evidence-only prototype
T60: Add GitHub Action Merge Evidence Report prototype
T61: Collect first 25 AI/code-review verification cases
T62: Add eval metrics for merge evidence quality
```

Current local status:

```text
T59 implemented
T60 implemented
T61 implemented
T62 implemented
verify eval useful merge evidence rate: 25/25 on the first fixture slice
```

## Success Metrics

M0 should measure:

- valid merge evidence JSON rate
- changed-file classification accuracy
- test recommendation usefulness
- dangerous change detection rate
- missing evidence recall
- report brevity
- reviewer acceptance
- time saved in review
- post-merge regression capture

North-star metric:

```text
Useful Merge Evidence Rate
```

Definition:

```text
Percent of PRs where Minerva correctly identifies the main verified evidence,
the main residual risk, and the next useful verification step.
```

## 90-Day Plan

### Days 1-14

- Define merge evidence schema.
- Implement diff summarization without model dependency.
- Generate static report from changed files and test logs.
- Run on Minerva itself.

### Days 15-30

- Add policy checks for risky files and dangerous commands.
- Add repository profile support.
- Add GitHub Action artifact and PR summary.
- Collect real PR verification cases.

### Days 31-60

- Add optional local model for impact/risk suggestions.
- Add test recommendation.
- Add missing-evidence classification.
- Add eval harness for report quality.

### Days 61-90

- Run across multiple open-source repositories.
- Compare with human review outcomes.
- Build first verification corpus.
- Publish Minerva Verify M0 report.

## Relationship To Agent OS Bootstrap

The bootstrap strategy depends on the verification strategy.

Before Minerva should run below the OS, it must first prove that it can produce
trustworthy evidence above the OS.

Sequence:

```text
PR verification -> CI/runtime verification -> Linux daemon -> rescue installer -> bootstrap layer
```

This path keeps ambition high while keeping proof loops short.

## Strategic Summary

The winning path is:

```text
Do not compete with coding agents.
Become the evidence layer beneath them.
```

If Minerva can make AI-generated code easier to verify, merge, deploy, and
recover from, then it earns the right to move downward into Linux runtime,
rescue images, and future agent-native computers.
