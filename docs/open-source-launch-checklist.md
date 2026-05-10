# Open-Source Launch Checklist

Use this checklist after PR #56 is reviewed and merged.

## Repository Settings

- Keep repository private until the launch PR is merged.
- Change repository visibility to public only after the launch PR lands.
- Set the repository description to:

```text
CPU-local reliability kernel for agents, CI/CD, and AIOps.
```

- Keep these topics:

```text
agent-safety
ai-agents
aiops
ci-cd
devtools
evals
local-llm
reliability
```

## Branch Protection

Protect `main` after the repository is public:

- require pull requests before merging
- require passing status checks
- block force pushes
- keep admin bypass explicit and rare

## Security Settings

Enable what the account or organization supports:

- Dependabot alerts
- secret scanning
- private vulnerability reporting

Security contact: `security@minervakernel.com`.

## Starter Issues

Create these first public issues after the repository becomes public.

### Add more redacted failure cases

```markdown
## Goal

Add small, redacted failure cases that improve Minerva's failure taxonomy and
eval coverage.

## Good starting points

- Python dependency failures
- shell command failures
- CI log failures
- schema/JSON failures
- permission failures

## Safety

Do not include secrets, private logs, customer data, full environment dumps, or
proprietary source.

## Validation

Run:

```bash
python3 -m unittest tests.test_failure_corpus tests.test_eval_smoke
python3 -m minerva_kernel.eval_smoke
```
```

### Add a real local CPU model benchmark artifact

```markdown
## Goal

Run the CPU model eval harness against a real local OpenAI-compatible provider
and publish a benchmark artifact that passes the evidence gate.

## Requirements

- local provider only
- no remote fallback
- no model weights committed to the repo
- artifact embeds `minerva.cpu_model_eval_report.v0`
- `scripts/check-cpu-benchmark-evidence.py` passes

## Validation

Run:

```bash
python3 scripts/check-cpu-benchmark-evidence.py <artifact>
```
```

### Add a GitHub Actions adapter event example

```markdown
## Goal

Add a CI-style adapter event example that maps a GitHub Actions failure into
`observation.v0` and reports a policy-gated Minerva decision.

## Requirements

- report-only behavior
- `execution.state=not_executed`
- no host status override
- redacted log tail

## Validation

Run:

```bash
python3 -m unittest tests.test_adapter_event_examples
```
```

### Add an agent framework adapter event example

```markdown
## Goal

Add an example event for an agent tool failure from a framework such as
LangGraph, Claude Code, Codex, Cursor, or AutoGen.

## Requirements

- no framework dependency in the core package
- adapter event wrapper only
- model decision is not authorization
- policy block reason is preserved

## Validation

Run:

```bash
python3 -m unittest tests.test_adapter_event_examples tests.test_adapter_implementation_checklist
```
```

### Improve minervad local diagnosis API docs

```markdown
## Goal

Improve docs and examples for local-only `minervad /diagnose` usage.

## Requirements

- localhost by default
- no service installation requirement
- no remote exposure
- no automatic action execution

## Validation

Run:

```bash
python3 -m unittest tests.test_daemon tests.test_minervad_smoke_script
python3 scripts/minervad-diagnose-smoke.py
```
```

## Launch Message

Suggested first public positioning:

```text
Minerva is a CPU-local reliability kernel for agents, CI/CD, and AIOps. It
turns failures into structured observations, policy-gated decisions, and eval
feedback loops. It is diagnostic by default: no auto-repair, no hosted service,
and no remote model requirement for the minimum path.
```
