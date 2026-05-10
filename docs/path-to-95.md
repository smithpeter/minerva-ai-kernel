# Path To 95

This document tracks the gap from an open-source-ready project to a highly
credible early infrastructure project.

## Current Strong Points

- Clear kernel: `observe -> diagnose -> policy gate -> report -> eval loop`.
- CPU-local minimum path.
- No auto-repair by default.
- `decision.v0`, `observation.v0`, policy decision, eval candidate, and review
  ledger contracts.
- `minervad /diagnose` local API.
- GitHub Action metadata for CI log diagnosis.
- Release dashboard and handoff tooling.
- 190+ local tests and CI smoke checks.

## Remaining Gap To 95

### Real-World Evidence

The highest-value missing proof is real usage evidence:

- 20-50 redacted CI failures from public repositories
- 3 sandbox or adopter repos using Minerva
- at least one real local CPU model benchmark artifact
- one agent-framework failure event example from a real workflow

### Product Entry

The first screen should stay focused on:

- diagnose a log
- understand a safe next step
- see that policy gates the result
- run eval smoke
- adopt in GitHub Actions

### Community Loop

The project should make contribution paths obvious:

- add failure cases
- add adapter events
- run local benchmark evidence
- improve minervad docs
- improve taxonomy mappings

## Target 95% Criteria

Minerva can be considered near 95% for early open-source launch when:

- PR #56 is merged and the repository is public.
- `main` is protected and CI is required.
- A first public release tag exists.
- `docs/five-minute-demo.md` works from a fresh checkout.
- The GitHub Action is usable from another repository.
- `scripts/check-cpu-benchmark-evidence.py` has at least one real passing
  artifact.
- At least 20 real redacted failure cases are reviewed.
- At least one external or sandbox repo records Minerva output in CI.

## Do Not Claim Yet

Until the criteria above are met, do not claim:

- autonomous repair
- full AIOps platform coverage
- production incident automation
- benchmark superiority for a specific small model
- broad framework support

The correct claim is narrower:

```text
Minerva makes agent and CI failures observable, policy-gated, and learnable.
```
