# CI Integration Surface

Date: 2026-05-08

This document defines the next GitHub Actions integration surface for Minerva:
a concise markdown job summary and a JSON artifact shape derived from
`minerva observe --`.

The surface is intentionally local and credential-free. It does not require
GitHub API credentials, does not post PR comments, and does not implement a
hosted service.

## GitHub Actions Pattern

Use `minerva observe --` around the command that should be interpreted. The
observed command remains the CI gate; Minerva's decision is diagnostic evidence,
not auto-repair.

```yaml
name: ci

on:
  pull_request:
  push:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install project
        run: python3 -m pip install -e .

      - name: Observe tests with Minerva
        shell: bash
        run: |
          set +e
          minerva observe -- python3 -m unittest discover -s tests
          minerva_status=$?

          run_record="$(ls -t .minerva/runs/*.json 2>/dev/null | head -n 1 || true)"
          if [ -z "$run_record" ]; then
            echo "# Minerva CI Summary" >> "$GITHUB_STEP_SUMMARY"
            echo "" >> "$GITHUB_STEP_SUMMARY"
            echo "Minerva did not write a run record." >> "$GITHUB_STEP_SUMMARY"
            exit "$minerva_status"
          fi

          python3 scripts/render-minerva-summary.py "$run_record" \
            >> "$GITHUB_STEP_SUMMARY"
          python3 scripts/render-minerva-artifact.py "$run_record" \
            > minerva-ci-run.json

          observed_status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["observation"]["exit_code"])' "$run_record")"
          exit "$observed_status"
```

Notes:

- The renderer script names are placeholders for the next implementation step.
  Static examples live in [minerva-ci-summary.md](../examples/minerva-ci-summary.md)
  and [minerva-ci-run-artifact.json](../examples/minerva-ci-run-artifact.json).
- Until a first-class renderer exists, the CI workflow can attach or print the
  raw `.minerva/runs/*.json` record produced by `minerva observe --`.
- The shell exits with the observed command exit code so Minerva cannot mask a
  failing test command.
- Artifact upload is optional and not required for the design. If enabled later,
  upload only the rendered JSON artifact and markdown summary, not full raw logs.

## Markdown Summary Contract

The markdown summary is written to `$GITHUB_STEP_SUMMARY`. It should fit on one
screen and answer four questions:

| Question | Field |
| --- | --- |
| What command was observed? | `command`, `cwd`, `duration_ms` |
| Did the command fail? | `observed_exit_code`, `status` |
| What did Minerva classify? | `failure`, `action`, `confidence`, `risk` |
| Was the decision safe to use? | `policy_decision.allowed`, `policy_decision.reason`, `redactions` |

Recommended sections:

1. Header with status.
2. Compact command table.
3. Failure interpretation.
4. Safety gate.
5. Bounded evidence excerpts.

The summary should never include full logs, full environment variables,
credential files, tokens, private keys, cookies, cloud credentials, or secret
values.

## JSON Artifact Contract

The CI artifact normalizes the local `run.v0` record into a CI-specific wrapper.
The proposed schema version is `minerva_ci_run.v0`.

Top-level fields:

| Field | Required | Notes |
| --- | --- | --- |
| `schema_version` | yes | Always `minerva_ci_run.v0` for this artifact. |
| `created_at` | yes | UTC timestamp for artifact rendering. |
| `ci` | yes | GitHub Actions metadata that is safe to persist. |
| `summary` | yes | Small summary used by dashboards and summaries. |
| `run_record` | yes | Redacted Minerva `run.v0` record. |
| `safety` | yes | Explicit safety posture for CI consumers. |

The `summary` object should include:

- `status`: one of `passed`, `failed_policy_allowed`, `blocked_by_policy`, or
  `minerva_error`.
- `observed_exit_code`: the observed command exit code.
- `failure`, `action`, `confidence`, `risk`, and `escalate` from the Minerva
  decision.
- `policy_allowed` and `policy_reason`.
- `redaction_count` and `redaction_types`.

The `safety` object must include:

- `auto_repair`: always `false` for this surface.
- `model_input_redacted`: `true` when the observation sent to the model has
  passed through redaction.
- `artifact_redacted`: `true` when persisted artifact text is redacted.
- `policy_gated`: `true` when the policy runtime has evaluated the decision.
- `github_api_credentials_required`: always `false`.

## Safety Notes

Minerva CI output is a diagnostic layer only.

- No auto-repair: CI must not execute the returned action automatically.
- Redaction before model input: stdout, stderr, command text, cwd, runtime
  metadata, decisions, and saved records must be redacted before model input and
  artifact persistence.
- Policy-gated decisions: consumers should trust only decisions with an explicit
  `policy_decision.allowed: true`; blocked decisions may still be useful as
  audit evidence.
- Bounded evidence: summaries and artifacts should include tails and selected
  metadata, not full logs or full environments.
- Credential-free by default: GitHub API tokens are not required for rendering a
  local summary or JSON artifact.

## Example Outputs

- Markdown summary: [examples/minerva-ci-summary.md](../examples/minerva-ci-summary.md)
- JSON artifact shape: [examples/minerva-ci-run-artifact.json](../examples/minerva-ci-run-artifact.json)
