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

## CPU Model Eval Harness v0

The first local-model eval harness lives in `minerva_kernel.cpu_model_eval` and
defaults to `evals/cpu_model_cases.jsonl`. The default path is deterministic:
it evaluates checked-in fixture decisions and can also be driven by
`MockModelProvider` in tests, so it does not require Ollama, GPU access,
network access, model weights, or package installation.

Run it without a real model:

```bash
python3 -m minerva_kernel.cpu_model_eval
```

Run it against a local OpenAI-compatible provider such as Ollama:

```bash
python3 -m minerva_kernel.cpu_model_eval \
  --provider local-openai \
  --model qwen2.5-coder:0.5b-instruct \
  --base-url http://localhost:11434/v1/chat/completions
```

This path measures per-case local provider latency and records the candidate
metadata in the report. It still reports `remote_models_used: false`; Minerva
does not call a remote model automatically when the local provider is
unavailable.

The JSON report uses the CPU model eval report shape from
`docs/sub-500m-cpu-model-plan.md` and the scoring definitions in
`docs/cpu-model-eval-scoring-contract.md`, including:

- `minerva.cpu_model_eval_report.v0` schema version.
- candidate and minimum-path metadata.
- corpus case mix.
- JSON validity, failure label accuracy, safe recovery decision rate,
  escalation quality, dangerous action rate, latency, and fallback behavior.
- per-case result fields for validity, failure, action, policy decision,
  dangerous action detection, escalation, safe recovery, fallback, latency, and
  notes.

Real Ollama or local GGUF execution is a later plug-in path: wire a local
provider into this harness only after the fixture and mock-provider path stays
green. The minimum eval path must continue to run offline.

## M0 Failure Corpus Slice

The first labeled M0 slice lives in `evals/failure_cases_m0_slice.json`.
It is a machine-readable JSON array of synthetic command/runtime failure
observations. The slice is not executed by tests and does not require network
access, Docker, npm, or package installs.

Each case contains:

- `id`: stable case identifier.
- `category`: one of `python`, `shell-cli`, `git`, `npm-node`,
  `docker-build`, `dns-network`, `permission`, `timeout`, `ci`,
  `model-api`, `schema-json`, or `secret-redaction`.
- `observation`: an `observation.v0` payload.
- `expected_failure`: the labeled failure diagnosis.
- `expected_action`: one Instruction Set v0 action.
- `policy_expectation`: expected read-only policy result and rationale.
- `rationale`: short reason the label and action are correct.
- `redaction_expectation`: required for `secret-redaction` cases, with minimum
  redaction count and required redaction types.

The loader in `minerva_kernel.failure_corpus` validates JSON/JSONL cases,
observation schema, category labels, action labels, duplicate IDs, policy
expectation, and redaction expectations for secret cases. Unit tests cover the
default slice and malformed fixtures.

The M1 metrics report is generated deterministically from local fixtures and
published in `evals/m1_eval_report.md`.

Run it without network or model access:

```bash
python3 -m minerva_kernel.eval_report --format json
python3 -m minerva_kernel.eval_report --format markdown
minerva eval-report --format json
```

Current corpus category counts after M1 growth:

| Category | Count |
| --- | ---: |
| `python` | 9 |
| `shell-cli` | 9 |
| `git` | 10 |
| `npm-node` | 9 |
| `docker-build` | 9 |
| `dns-network` | 9 |
| `permission` | 9 |
| `timeout` | 9 |
| `ci` | 10 |
| `model-api` | 10 |
| `schema-json` | 10 |
| `secret-redaction` | 9 |

Contribution target: keep every required category at 8 or more validated
cases, then grow each category toward 15 short, redacted examples before
adding larger generated teacher-labeled corpora.

## Eval Candidate Data Loop

Saved `run.v0` records can be rendered into review-only eval candidate JSONL:

```bash
minerva render-eval-candidates .minerva/runs/<run-id>.json > eval-candidates.jsonl
```

The output schema is `minerva_eval_candidate.v0`. It includes the redacted
observation, model decision, policy decision, suggested expected labels, and a
`review.status` of `needs_human_review`.

Candidate artifacts are not approved corpus cases. They must be reviewed,
labeled, de-duplicated, and manually adapted before being copied into
`evals/cpu_model_cases.jsonl` or other official corpora. The command does not
upload data, call remote models, or modify eval fixtures.

Human review decisions can be recorded in a ledger JSONL using
`minerva_eval_candidate_review.v0`. See
`evals/eval_candidate_ledger.example.jsonl` for accepted, rejected, and
deferred examples.

Validate a ledger locally:

```bash
minerva validate-eval-ledger evals/eval_candidate_ledger.example.jsonl
```

An accepted review must name the reviewer, review time, notes, and final
expected labels. Rejected and deferred reviews must keep
`approved_for_corpus=false` and must not include final expected labels. The
ledger is review evidence only; it does not mutate official corpora.
