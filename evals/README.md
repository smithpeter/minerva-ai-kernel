# Evals

Evaluation for Minerva's failure interpretation behavior.

The first benchmark target is:

```text
Safe Recovery Decision Rate
```

Measured by:

- valid structured output
- failure classification accuracy
- safe action accuracy
- escalation recall
- dangerous action rate
- CPU latency

## Smoke Runner v0

The initial deterministic smoke corpus lives in `evals/smoke_cases.jsonl`.
Each JSONL case contains:

- `observation`: an `observation.v0` payload.
- `decision`: the mock-provider `decision.v0` payload to evaluate.
- `expected`: the expected failure label, safe action, policy result, and
  optional redaction assertions.

Run it without network access:

```bash
python3 -m minerva_kernel.eval_smoke
```

## M0 Failure Corpus Slice

The first labeled M0 slice lives in `evals/failure_cases_m0_slice.json`.
It is a machine-readable JSON array of synthetic command/runtime failure
observations. The slice is not executed by tests and does not require network
access, Docker, npm, or package installs.

Each case contains:

- `id`: stable case identifier.
- `category`: one of `python`, `shell-cli`, `npm-node`, `docker-build`,
  `dns-network`, `permission`, `timeout`, or `secret-redaction`.
- `observation`: an `observation.v0` payload.
- `expected_failure`: the labeled failure diagnosis.
- `expected_action`: one Instruction Set v0 action.
- `policy_expectation`: expected read-only policy result and rationale.
- `rationale`: short reason the label and action are correct.
- `redaction_expectation`: required for `secret-redaction` cases, with minimum
  redaction count and required redaction types.

The loader in `minerva_kernel.failure_corpus` validates JSON/JSONL cases,
observation schema, category labels, action labels, policy expectation, and
redaction expectations for secret cases. Unit tests cover the default slice and
malformed fixtures.
