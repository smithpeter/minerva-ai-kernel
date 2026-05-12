# Architecture

This document has two parts. **Current (M0)** describes what is implemented
and tested today. **Target (M2+)** describes the shape the roadmap is
heading toward. Sections labelled 🚧 are deliberately deferred.

## Current (M0) Shape

```text
Application Code
      |
      v
Minerva SDK / CLI  ── observe.py  ── observation.v0
      |
      v
Redaction (redaction.py, before any model sees text)
      |
      v
       ┌── no provider ──► baseline.propose_baseline_decision
Decide ┤                      (deterministic CPU-local interpreter)
       └── provider     ──► planner.build_prompt
                            └── router.LocalLLMRouter
                                 └── LocalOpenAICompatibleProvider (HTTP)
      |
      v
Policy Engine (policy.py — closed instruction set + read-only allow-list)
      |
      v
Diagnosis (decision + policy_decision + redactions)
      |
      v
Run record  →  .minerva/runs/*.json  →  CI summary / artifact renderer
```

### Components as implemented

#### SDK / CLI

`sdk.Minerva` and `minerva_kernel.cli.main` are the only entry points
application code uses. They hide whether a provider is configured.

#### Redaction

`redaction.redact_value` is applied to every observation before it reaches
the planner. The 16 credential patterns in `policy.CREDENTIAL_PATTERNS`
are stripped from stdout/stderr tails and runtime fields, never from a
separate post-model pass.

#### Baseline interpreter

`baseline.propose_baseline_decision` is the **default decide path** when no
provider is configured. It is a deterministic pattern matcher over
exit code, runtime flags, and combined stdout/stderr text, returning a
Decision from `INSTRUCTION_SET_V0`. This path requires no network, no
model weights, and no Python dependencies beyond the standard library.

#### Planner

`planner.build_prompt` turns a redacted Observation into a two-message
chat payload (system + user). The system message names the closed
instruction set and forbids shell/auto-repair output; the user message
serialises the Observation as JSON. It is intentionally thin — schema
discipline is enforced downstream by the Policy Engine, not by prose.

#### Router 🚧 (partial)

`router.LocalLLMRouter` currently wraps a single
`LocalOpenAICompatibleProvider`. **Multi-model selection by
availability / latency / task type is target shape, not current code.**
See the Target section below for the planned selector.

#### Policy Engine

`policy.validate_action` is the single authoriser. It enforces:

- action is in `INSTRUCTION_SET_V0` (14 closed actions)
- action label is not in `DANGEROUS_ACTION_LABELS` (10 entries)
- tool field, if present, is not in `WRITE_TOOLS` ∪ `SHELL_TOOLS`
- referenced commands do not match `DESTRUCTIVE_COMMAND_PATTERNS`
- credential paths from `CREDENTIAL_PATTERNS` are blocked

Tests in `tests/test_policy.py` cover each rejection class.

#### Executor

`executor.execute_action` runs **only** read-only diagnostic actions from
`policy.READ_ONLY_ACTIONS` (12 entries: check_dns, check_port,
inspect_file, etc.). It is never invoked automatically by `observe` —
the user must explicitly run `minerva execute-action <decision.json>`
and the action is re-validated by the policy engine at execution time.

#### Run records / CI rendering

`observe.save_run_record` writes `.minerva/runs/*.json`.
`ci_render.render_markdown_summary_from_file` and
`render_ci_artifact_json_from_file` turn a record into the
GitHub-Actions step summary and a redacted JSON artifact.

## Target (M2+) Shape

The pieces below are planned but **not implemented** today. Do not read
them as descriptions of current behaviour.

### Router selector 🚧

A real `Router` would choose a provider based on:

- availability (provider health probe result)
- latency budget (per-call timeout, p95 history)
- task type (e.g. JSON-only vs free-form)
- context length vs model context window
- previous failure history for this case category
- confidence requirement from the caller
- network status (offline → baseline only)

Today the router picks the only provider it was constructed with.
Adding the selector is gated on M2's CPU model bench publishing real
performance numbers across at least two candidates.

### Stronger-model escalation 🚧

`ask_bigger_llm` is in `INSTRUCTION_SET_V0` but there is no
auto-escalation wire-up. A future step would route low-confidence
decisions to a larger model behind explicit user opt-in, never
automatically.

### Observation store as operational memory 🚧

Run records exist as files. A future step would index them so the
router can learn which provider performs well on which failure
category. There is no such index today.

## Non-Negotiable Invariants

These hold in both the Current and Target shapes:

```text
LLM interprets. Policy authorizes. Executor acts.
```

- CPU-only minimum runtime; no GPU dependency.
- Zero runtime dependencies (`pyproject.toml` keeps `dependencies = []`).
- No automatic remote-LLM fallback. If a configured provider is
  unreachable, the baseline runs — the network is never reached
  silently.
- Redaction happens before any model input, not after.
- Decisions are structured. Free-text rationale is explanatory; the
  action field is the only execution channel and it is closed.
- `observe` ends with a run record. `execute-action` is a separate,
  explicit command.
