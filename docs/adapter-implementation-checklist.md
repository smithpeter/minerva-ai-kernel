# Adapter Implementation Checklist

Use this checklist before publishing a CI, AIOps, agent, gateway, editor, or
device adapter for Minerva.

## 1. Event Mapping

- Map one host failure event to one bounded `observation.v0`.
- Populate every required observation field: command, cwd, exit_code,
  stdout_tail, stderr_tail, duration_ms, source, and policy_summary.
- Keep `source` namespaced to the adapter, for example
  `adapter.github_actions` or `adapter.aiops_webhook`.
- Put only compact metadata in `runtime`, such as job name, event id, service
  name, timeout state, or network status.

## 2. Redaction Boundary

- Redact before model input.
- Redact before writing adapter events, CI annotations, incident notes, or
  debug artifacts.
- Never include raw tokens, private keys, full environment dumps, customer
  data, proprietary source, or full logs in examples.
- Add at least one test where secret-like input becomes a redacted marker.

## 3. Diagnosis Surface

- Use the stable local surfaces first:

```bash
minerva diagnose observation.json
```

or:

```bash
curl -X POST http://127.0.0.1:8765/diagnose \
  -H 'Content-Type: application/json' \
  --data @observation.json
```

- Treat invalid observations as adapter bugs and fail with a clear local error.
- Treat Minerva-unavailable errors as reportable host diagnostics, not as a
  reason to hide the original failure.

## 4. Policy Gate

- Treat `decision.v0` as model output, not authorization.
- Check `policy_decision.allowed` before considering any host action.
- Preserve `policy_decision.reason` in CI summaries, incident notes, or agent
  traces.
- When policy blocks, report the block and stop.
- Do not widen policy from an adapter package.

## 5. Report-Only Default

- Keep `adapter_executes_actions=false` by default.
- Keep `execution.state=not_executed` for adapter event reports.
- Do not override the original CI job or platform failure status.
- Do not automatically run shell commands, edit files, install packages,
  restart services, roll back deployments, or change credentials.

## 6. Tests

Minimum tests for a publishable adapter:

- valid host event becomes valid `observation.v0`
- invalid or incomplete host event is rejected
- secret-like input is redacted before persistence
- valid Minerva response is reported without execution
- policy-blocked Minerva response is reported with block reason
- Minerva-unavailable path preserves the original host failure

## 7. Release Notes

Adapter release notes should state:

- supported host platform and versions
- Minerva schema versions used
- whether the adapter calls CLI, SDK, or `minervad`
- optional dependencies
- where logs and artifacts are written
- that no hosted Minerva control plane or remote model is required for the
  minimum path
