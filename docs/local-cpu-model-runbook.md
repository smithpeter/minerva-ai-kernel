# Local CPU Model Runbook

Date: 2026-05-10

## Goal

Produce repeatable evidence for sub-500M CPU-local Minerva controller
candidates without downloading models in CI, shipping model weights, or
claiming fixture results as real benchmarks.

## Preconditions

- The candidate exists in
  [`models/cpu_model_candidates.json`](../models/cpu_model_candidates.json).
- License and provenance notes have been reviewed for the exact upstream model.
- The local runtime is CPU-only for the measured run.
- The eval corpus is the reviewed CPU controller corpus in
  [`evals/cpu_model_cases.jsonl`](../evals/cpu_model_cases.jsonl).
- The scoring rules are
  [`docs/cpu-model-eval-scoring-contract.md`](cpu-model-eval-scoring-contract.md).

## Ollama / OpenAI-Compatible Run

Start the local provider outside this repository:

```bash
ollama serve
ollama pull qwen2.5-coder:0.5b-instruct
```

Run the eval:

```bash
python3 -m minerva_kernel.cpu_model_eval \
  --provider local-openai \
  --model qwen2.5-coder:0.5b-instruct \
  --base-url http://localhost:11434/v1/chat/completions \
  --candidate-name qwen2.5-coder:0.5b-instruct \
  --parameter-count 0.49B \
  --runtime ollama-openai-compatible \
  --quantization "ollama default" \
  --device cpu \
  > evals/cpu-model-reports/qwen2_5_coder_0_5b_instruct.local.json
```

The report is valid only for the machine, runtime, corpus, prompt, and provider
settings used in the command. Record cold-start/warm-start context in a sibling
note if latency is compared.

## Future GGUF / llama.cpp Run

When a GGUF adapter exists, use the same report contract:

```text
candidate registry entry
  -> local GGUF file outside git
  -> llama.cpp provider adapter
  -> python3 -m minerva_kernel.cpu_model_eval
  -> cpu_model_eval_report.v0 artifact
```

Do not commit GGUF files or downloaded model artifacts to this repository.

## Artifact Naming

Use:

```text
evals/cpu-model-reports/<candidate-id>.<runtime>.json
```

Examples:

```text
evals/cpu-model-reports/qwen2_5_coder_0_5b_instruct.local.json
evals/cpu-model-reports/smollm2_360m_instruct_gguf.local.json
```

## Required Evidence

Each real candidate artifact must preserve:

- exact command used to generate the report
- candidate id from the registry
- provider model name
- provider base URL or local process path
- corpus path and case count
- scoring contract path
- `minimum_path.remote_models_used == false`
- `minimum_path.gpu_used == false`
- JSON validity, failure label accuracy, safe recovery rate, escalation
  quality, dangerous action rate, latency, and fallback behavior
- final decision: `promote`, `retest`, or `reject`

Fixture reports are useful for harness regression, but they are not model
benchmarks. A public model claim requires a real local provider report and
human review of candidate metadata, license/provenance, and failure clusters.

## Benchmark Evidence Gate

Validate a real benchmark artifact before making any model-performance claim:

```bash
python3 scripts/check-cpu-benchmark-evidence.py evals/cpu-model-reports/<candidate>.artifact.json
```

The gate rejects `evals/cpu_model_report_artifact.example.json` because that
file is only an example contract. A passing artifact must set
`artifact_status=real_local_benchmark`, `benchmark_claim=true`, embed a
`minerva.cpu_model_eval_report.v0` report, use a non-fixture local runtime,
meet the minimum case count, report all required metrics, and keep
`gpu_used=false`, `remote_models_used=false`, and
`model_weights_shipped_by_minerva=false`.

## Failure Handling

```text
local provider unavailable
  -> structured local fallback
  -> remote_fallback_attempts remains 0
  -> report decision is retest/reject, never an automatic remote call
```

Invalid JSON or schema failure from a local model is scored as an eval miss. It
must not be repaired silently by the harness.
