# Models

Model artifacts are not committed by default.

Target runtime:

```text
CPU-only
sub-500M parameters
GGUF
structured output
```

The CPU-local research registry lives in
[`models/cpu_model_candidates.json`](cpu_model_candidates.json). It records
candidate metadata only: parameter count, runtime path, quantization
expectation, hardware target, license/provenance notes, and provider command.

The registry does not download model weights, commit model artifacts, or claim
benchmark results. Score candidates with the
[`CPU Model Eval Scoring Contract`](../docs/cpu-model-eval-scoring-contract.md)
before treating any candidate as promoted.

Use the
[`Local CPU Model Runbook`](../docs/local-cpu-model-runbook.md) for repeatable
local candidate reports. The example artifact contract is
[`evals/cpu_model_report_artifact.example.json`](../evals/cpu_model_report_artifact.example.json);
it is not a benchmark result.

Use `scripts/check-cpu-benchmark-evidence.py` before making any real local
model benchmark claim. The gate rejects example or fixture artifacts and only
passes when a real local provider report is embedded with the required metrics
and minimum-path flags.
