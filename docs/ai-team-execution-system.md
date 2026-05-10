# AI Team Execution System

Date: 2026-05-08

## Core Question

How can an AI team implement Minerva without requiring the founder to push every step manually?

The answer is:

```text
turn the product strategy into an executable operating system for AI contributors
```

This requires:

- strict project boundaries
- machine-checkable requirements
- issue-driven work
- CI-gated acceptance
- role-specific agents
- automatic reporting
- controlled GitHub automation
- ecosystem tasks as first-class work

## Most Important Principle

AI teams do not fail mainly because they cannot write code.

They fail because:

- the target is ambiguous
- tasks are too large
- acceptance criteria are missing
- there is no eval gate
- agents edit unrelated files
- strategy drifts
- no one converts outcomes into next tasks

Therefore, Minerva must be run as:

```text
spec -> issue -> Plan-Eng Review -> branch -> tests/evals -> PR -> review -> merge -> next issue
```

The Plan-Eng Review gate is defined in
[`docs/plan-eng-review-workflow.md`](plan-eng-review-workflow.md). For
non-trivial code, eval, integration, security, release, or workflow tasks, the
AI worker must make the architecture, data flow, state/fallback paths,
failure modes, and test plan explicit before editing files.

When the active queue reaches zero pending tasks, use the
[AI-team stabilization criteria](ai-team-stabilization.md) before adding more
scope. Stabilization focuses on failed checks, evidence gaps, release handoff,
and explicit user requests.

## Non-Negotiable Boundaries

AI contributors must work only in:

```text
/Users/zouyongming/projects/minerva-ai-kernel
```

On Linux or another host, the equivalent repository root must be provided
explicitly with:

```bash
export MINERVA_PROJECT_ROOT=/path/to/minerva-ai-kernel
```

The boundary remains strict: the AI worker may operate only inside the declared
Minerva root.

They must not touch:

```text
/Users/zouyongming/VoxSign
/Users/zouyongming/VoxSign-decide-review
```

except when an issue is explicitly labeled:

```text
voxsign-integration
```

## Required Repository Structure

```text
minerva-ai-kernel/
  README.md
  ROADMAP.md
  CONTRIBUTING.md
  SECURITY.md
  GOVERNANCE.md
  docs/
  minerva_kernel/
  evals/
    failure-cases/
    run_eval.py
  taxonomies/
  policies/
  examples/
  adapters/
  scripts/
  .github/
    ISSUE_TEMPLATE/
    workflows/
```

## AI Team Roles

### Product Agent

Owns:

- roadmap
- issue creation
- prioritization
- release scope
- user value review

### Research Agent

Owns:

- related work
- small model benchmark tracking
- failure taxonomy research
- distillation plan

### Kernel Agent

Owns:

- observation schema
- decision schema
- router
- policy runtime
- safe action mapping

### Eval Agent

Owns:

- failure corpus
- eval runner
- benchmark reports
- regression gates

### Integration Agent

Owns:

- CLI wrapper
- CI integration
- SDK
- daemon API later

### Security Agent

Owns:

- redaction
- policy boundaries
- dangerous action tests
- threat model

### Docs Agent

Owns:

- README
- quickstart
- examples
- architecture docs
- contributor docs

### Growth Agent

Owns:

- launch content
- GitHub issues for community
- blog posts
- examples
- ecosystem outreach
- benchmark leaderboard content

## Issue Types

Every task must be an issue with one type:

```text
spec
code
eval
dataset
security
docs
integration
growth
release
research
```

Every issue must include:

- goal
- allowed files
- non-goals
- acceptance criteria
- test/eval command
- risk notes

New local task cards should start from
[`docs/ai-team-task-template.md`](ai-team-task-template.md), which includes the
Plan-Eng Review block and the completion gate for critical failure-mode gaps.

For substantial implementation tasks, the task output or PR body must also
include a Plan-Eng Review block with:

- scope challenge
- what already exists
- explicit non-scope
- ASCII data-flow or state diagram
- failure-mode table
- test/eval plan
- parallelization or sequential-execution note

## Acceptance Criteria Standard

No issue is complete unless it has at least one of:

- unit test
- eval case
- CLI demo
- documentation update
- benchmark report
- security test

For product-critical issues, require:

```text
user-visible value statement
```

Example:

```text
After this issue, a user can run `minerva observe -- pytest`
and receive a structured diagnosis saved to `.minerva/runs/`.
```

For engineering-critical issues, require:

```text
no critical Plan-Eng failure-mode gap remains open
```

A critical gap means there is no test/eval, no error handling, and the user
would see a silent failure.

## AI Autonomy Levels

### Level 0: Suggest

AI proposes tasks and plans.

### Level 1: Draft

AI opens issues and writes docs.

### Level 2: Implement

AI creates branches and PRs.

### Level 3: Verify

AI runs tests/evals and updates PR with results.

### Level 4: Maintain

AI creates next issues based on failures and roadmap.

### Level 5: Publish

AI prepares releases and launch materials.

Human approval remains required for:

- merge to main
- publishing package
- creating public GitHub repository under founder account/org
- changing security policy
- enabling external network integrations
- VoxSign integration

## GitHub Automation

AI team should be able to create:

- repository skeleton
- issue templates
- PR templates
- labels
- milestones
- project board
- GitHub Actions workflows
- benchmark artifacts
- release drafts

Do not allow AI to silently:

- merge PRs
- publish packages
- upload secrets
- modify repository permissions
- connect production systems

## GitHub Labels

Recommended labels:

```text
area:cli
area:kernel
area:eval
area:dataset
area:policy
area:security
area:docs
area:ci
area:integration
area:growth
area:model
priority:p0
priority:p1
priority:p2
good first issue
needs-human-review
blocked
voxsign-integration
```

## GitHub Actions Required

Minimum CI:

```text
lint
unit tests
eval smoke test
schema validation
dangerous action test
docs link check
```

Critical gate:

```text
dangerous action test must never fail open
```

## Weekly Autonomous Loop

AI team should run this cycle:

```text
Monday: inspect roadmap, create/refresh issues
Daily: implement top scoped issues
Every PR: run tests/evals, update report
Friday: publish weekly progress report
After failures: create follow-up issues automatically
After new eval data: update benchmark report
```

Founder should only need to review:

- weekly summary
- high-risk decisions
- merges/releases
- strategic pivots

## Product Direction Guardrail

Every weekly report must answer:

```text
Did this week improve CPU-local failure interpretation?
Did this week improve corpus/eval quality?
Did this week improve user first-run value?
Did this week preserve safety boundaries?
```

If no, the work is likely drifting.

## Growth And Ecosystem Automation

AI team should create:

- failure case contribution guide
- public benchmark page
- "submit your CI failure" template
- GitHub Actions demo
- blog post drafts
- comparison tables
- model leaderboard
- adapter roadmap
- community good-first-issues

Growth tasks should be treated like product work, not afterthoughts.

## First 20 Issues

The AI team should create and execute these first:

1. Create repository skeleton.
2. Write README quickstart.
3. Define Observation Schema v0.
4. Define Decision Schema v0.
5. Define Minerva Instruction Set v0.
6. Implement `minerva diagnose failure.json`.
7. Implement `minerva observe -- <command>`.
8. Add redaction v0.
9. Add policy runtime v0.
10. Add safe action mapping v0.
11. Add 30 Python failure cases.
12. Add 30 shell/CLI failure cases.
13. Add 30 npm/Node failure cases.
14. Add 30 Docker failure cases.
15. Add eval runner v0.
16. Benchmark Qwen2.5-Coder-0.5B.
17. Benchmark SmolLM2-360M.
18. Benchmark SmolLM2-135M.
19. Add GitHub Actions smoke test.
20. Draft launch blog post.

## Success Condition For AI Team

The AI team is working if it can produce weekly progress without founder step-by-step prompting:

```text
new issues -> PRs -> tests/evals -> reports -> next issues
```

The founder should steer strategy, not manually push every task.
