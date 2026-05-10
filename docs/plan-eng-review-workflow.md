# Plan-Eng-Review Workflow

Date: 2026-05-10

## Source

This workflow adapts the Plan-Eng-Review pattern discussed in Saito's X post:

```text
https://x.com/SaitoWu/status/2052968430685573379
```

The public X page exposes the core point: do planning first, draw ASCII
diagrams for data flow, user flow, and state machines, then implement, review,
and test. The same direction is reflected in Garry Tan's gstack
`plan-eng-review` skill, which positions engineering review as the step that
locks architecture, data flow, diagrams, edge cases, test coverage, and
performance before coding.

## Current Minerva Operating Model

Minerva already has several strong execution controls:

- task cards with allowed files, non-goals, acceptance criteria, and test/eval
  commands
- role lanes for product, research, kernel, eval, integration, security, docs,
  growth, and release work
- strict repository boundaries and contamination checks
- CI-style gates through compile, unit tests, eval smoke, release readiness,
  and policy tests
- an AI-team timer that runs bounded task ticks and refuses dirty worktrees

The gap is not raw implementation ability. The gap is that the work can still
move from task text directly into edits before the agent has made the system
shape explicit. That creates predictable failure modes:

- hidden assumptions about data flow or state transitions
- tests added after implementation instead of derived from the plan
- missing negative paths and silent-failure handling
- role mixing: product scope, engineering design, implementation, review, and
  release decisions collapse into one pass
- parallel work launched before module boundaries and dependencies are clear

## Minerva Adaptation

Minerva's default AI-team loop becomes:

```text
task intake
  -> scope challenge
  -> engineering plan with ASCII diagrams
  -> failure-mode and test plan
  -> implementation
  -> diff review
  -> verification
  -> task output / PR or commit
```

For non-trivial code, eval, integration, security, release, or workflow tasks,
the worker must produce a concise Plan-Eng Review before editing project files.
For trivial documentation or metadata edits, the worker may use the lightweight
version, but still must state what is not in scope and how it will verify the
change.

## Required Plan-Eng Review Block

Each substantial task should include this block in the task output or PR body:

````markdown
## Plan-Eng Review

### Scope Challenge
- Accepted scope:
- Reduced or deferred scope:

### What Already Exists
- Existing code/docs reused:
- Existing tests/evals reused:

### NOT In Scope
- Deferred:

### Architecture / Flow
```text
input
  -> component
  -> policy/eval/check
  -> persisted output
```

### State / Decision Diagram
```text
[start] -> [validated] -> [implemented] -> [verified]
              |               |
              v               v
           [blocked]       [needs fix]
```

### Failure Modes
| Failure mode | Covered by test/eval | Error handling | User-visible outcome |
| --- | --- | --- | --- |
| Example timeout or invalid input | yes/no | yes/no | clear/silent |

### Test / Eval Plan
- Required command:
- Additional focused check:

### Parallelization
- Sequential because:
- Parallel lanes, if any:

### Review Readiness
- Diff review focus:
- Release or docs impact:
````

## ASCII Diagram Rules

Use ASCII diagrams when the change has any of:

- more than one component boundary
- a user-visible or CLI flow
- a state machine or retry/fallback path
- a policy, security, redaction, or executor boundary
- eval scoring, corpus loading, or report generation
- release automation or timer/autopilot behavior

Keep diagrams small enough to maintain. Diagrams are part of the change: if a
nearby diagram becomes stale, update it in the same task.

## Failure-Mode Gate

For each new code path, list one realistic production failure mode. A critical
gap exists when all three are true:

```text
no test/eval covers it
no error handling exists
the user would see a silent failure
```

Critical gaps block marking a task done unless the task explicitly documents
why the gap is accepted and what follow-up task owns it.

## Review Separation

Planning is not implementation. Implementation is not review. Review is not
shipping.

Minerva uses these role boundaries:

- Product review: confirms user value, scope, and non-goals.
- Engineering plan review: confirms architecture, data flow, state, tests, and
  failure modes before edits.
- Implementation: makes the smallest coherent change that satisfies the plan.
- Diff review: looks for regressions, unsafe behavior, missing tests, and stale
  docs after edits.
- Verification: runs the listed tests/evals and records exact commands.
- Ship/finalize: commits, pushes, opens or updates PRs only after verification.

## Automation Rules

The timer and agent loop should remind workers to read this workflow before
editing. Autopilot remains conservative: passing tests are required, but tests
do not replace the Plan-Eng Review block for substantial work.

When future orchestration is considered, Minerva should not add more agent
framework complexity until the single-worker Plan-Eng-Review loop is reliable.
Parallel workers are useful only after module boundaries, dependencies, and
merge-conflict risks are explicit.
