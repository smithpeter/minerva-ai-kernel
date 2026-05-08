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
