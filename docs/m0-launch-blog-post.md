# Minerva M0 Launch Blog Post Draft

Draft status: not published.

Public project domain: `minervakernel.com`

## Title

Minerva M0: A CPU-Local Failure Interpreter For CI/CD, Agents, And Ops

## Post

Modern software systems increasingly depend on chains of tools, agents, model calls,
CI jobs, scripts, containers, and network services. When one link fails, the failure
state is often scattered across stdout, stderr, exit codes, runtime context, logs,
configuration, and policy boundaries. The system may know that something failed,
but not what kind of failure it is, what evidence matters, or which next action is
safe.

Minerva is a CPU-local failure interpreter for CI/CD, agents, and ops. The project
is published at `minervakernel.com`.

M0 is the first milestone: a local failure interpreter loop. It starts with one
plain command:

```bash
minerva observe -- <command>
```

M0 runs the command, captures bounded stdout and stderr tails, records the exit
code and runtime context, builds an Observation Schema v0 payload, asks a local
interpreter for a structured Decision Schema v0 response, validates that response
against the read-only policy runtime, and saves a run record under `.minerva/runs/`.

That sounds small by design. Minerva is not trying to replace CI, monitoring,
incident platforms, or developer judgement. M0 is the minimum useful kernel loop:

```text
observe command -> structure failure state -> propose bounded decision -> policy-check -> save record
```

The positioning is intentionally narrow:

```text
Minerva: CPU-local failure interpreter for CI/CD, agents, and ops.
```

The long-term category is an AI reliability kernel: a local layer that lets
systems fail with more structure, more evidence, and stricter safety boundaries.
M0 proves the first unit of that category without promising broad autonomy.

## What M0 Can Do

M0 can observe commands such as:

```bash
minerva observe -- pytest
minerva observe -- npm test
minerva observe -- docker build .
```

For each run, Minerva can:

- capture command, working directory, exit code, duration, stdout tail, stderr tail, and runtime metadata
- redact known sensitive values before model input and saved records
- serialize observations as `observation.v0`
- serialize decisions as `decision.v0`
- policy-check the proposed action with a default read-only policy
- save a `run.v0` record for review, debugging, and future eval work
- run deterministic smoke evals for the current M0 corpus

The useful artifact is not an automatic fix. The useful artifact is a structured,
policy-checked failure record that can be inspected, evaluated, and improved.

## Safety Boundaries

M0 is read-only by default. The model can propose bounded labels such as
`check_logs`, `inspect_dependencies`, `check_command_exists`, or
`check_permissions`; deterministic policy decides whether that proposal is allowed.
The policy runtime fails closed on write tools, shell tools, destructive commands,
credential access, unknown action labels, low confidence, higher risk, and
escalation requests.

The project principle is:

```text
LLM interprets. Policy authorizes. Executor acts.
```

For M0, the executor does not perform repair. It observes, records, validates, and
stops at a safe boundary.

## Explicit Non-Claims

- M0 does not auto-repair systems.
- M0 is not a full AIOps platform.
- M0 does not require a remote LLM for minimum function.
- M0 does not execute arbitrary model-generated shell commands.
- M0 does not replace tests, CI, monitoring, or human review.

These non-claims are product constraints, not missing marketing. The point of M0 is
to make the smallest useful loop safe enough to evaluate.

## Why CPU-Local Matters

Failures often happen when the comfortable path is unavailable: the network is
down, a hosted model API is unreachable, CI is isolated, a GPU is not present, or
an agent loop is already degraded. A reliability kernel should keep a minimum
reasoning path alive in those conditions.

CPU-local does not mean "no intelligence." It means the first response path should
fit inside constrained developer and ops environments. A small local model,
strict schemas, narrow action labels, deterministic policy, and eval-led iteration
are a better M0 target than a broad autonomous agent that needs cloud access and
permission to modify the machine.

## Demo Path

The M0 demo is deliberately short:

```bash
minerva observe -- python3 -c 'import sys; print("ImportError: No module named yaml", file=sys.stderr); sys.exit(3)'
```

Then inspect the saved run record:

```bash
ls -t .minerva/runs/*.json | head -1
```

The record contains:

- `schema_version: run.v0`
- an `observation.v0` command record
- a `decision.v0` proposed action
- a deterministic `policy_decision`

Finally, run the smoke eval:

```bash
python3 -m minerva_kernel.eval_smoke
```

Expected current signal:

```text
Minerva eval smoke v0
Cases: 5/5 passed, 0 failed
Safe Recovery Decision Rate: 5/5 (100.0%)
```

## Read More

- [M0 release readiness checklist](m0-release-readiness.md)
- [Product strategy](product-strategy.md)
- [Architecture](architecture.md)
- [Observation Schema v0](observation-schema-v0.md)
- [Decision Schema v0](decision-schema-v0.md)
- [Failure case contribution guide](failure-case-contributions.md)
- [M0 demo script](../examples/m0-demo-script.md)
