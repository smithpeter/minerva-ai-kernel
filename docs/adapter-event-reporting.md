# Adapter Event Reporting

External CI, AIOps, and agent platforms can embed Minerva without adopting a
hosted control plane. The adapter boundary is a report-only contract:

```text
platform event
  -> observation.v0
  -> minerva diagnose or POST /diagnose
  -> decision.v0 + policy_decision
  -> platform annotation or escalation note
```

The model decision is not authorization. Adapters must check
`policy_decision.allowed` before considering any host action, and the default
adapter behavior is to report only.

Before implementing a concrete adapter, use the
[adapter implementation checklist](adapter-implementation-checklist.md).

## Event Shape

Machine-readable examples live in
[`examples/adapter-events`](../examples/adapter-events):

- `ci-job-failure.adapter-event.json`
- `aiops-service-rollback.adapter-event.json`

The example wrapper uses `minerva.adapter_event.v0`:

```json
{
  "schema_version": "minerva.adapter_event.v0",
  "producer": {
    "adapter": "github-actions-example",
    "version": "0.1.0"
  },
  "platform": {
    "type": "ci",
    "name": "GitHub Actions"
  },
  "event": {
    "id": "run-1001-job-test",
    "kind": "job_failed",
    "summary": "Python test job failed during dependency import."
  },
  "observation": {
    "schema_version": "observation.v0"
  },
  "diagnosis": {
    "decision": {
      "schema_version": "decision.v0"
    },
    "policy_decision": {
      "allowed": true,
      "reason": "allowed by read-only policy"
    },
    "execution": {
      "state": "not_executed",
      "reason": "adapter reports diagnostics only"
    }
  },
  "reporting": {
    "consumer_action": "annotate_ci_job",
    "policy_is_authorization": true,
    "adapter_executes_actions": false,
    "host_status_override": false
  }
}
```

The wrapper is intentionally small. The stable contracts inside it are
`observation.v0`, `decision.v0`, and the policy decision fields.

## Producing Observations

Adapters should map host failures into bounded `observation.v0` fields:

- `command`: the failed command, job, tool call, or event summary.
- `cwd`: the workspace or event namespace, not a private full environment dump.
- `exit_code`: the host exit code when available, or `1` for failed events.
- `stdout_tail` and `stderr_tail`: compact redacted tails, not full logs.
- `source`: adapter identifier such as `adapter.github_actions`.
- `policy_summary`: a plain statement of what the adapter captured and what it
  must not do automatically.
- `runtime`: small metadata such as job name, event id, service name, timeout
  state, or `network_status`.

If an adapter cannot populate required observation fields, it should reject the
event as an adapter bug and report a clear local error. It should not invent
missing logs or repair malformed model output.

## Consuming Decisions

Adapters can call one of the existing local surfaces:

```bash
minerva diagnose observation.json
```

or, when `minervad` is explicitly started:

```bash
curl -X POST http://127.0.0.1:8765/diagnose \
  -H 'Content-Type: application/json' \
  --data @observation.json
```

The adapter can then annotate the host platform with:

- failure label
- proposed action label
- confidence, risk, and escalation flag
- policy allowed or blocked
- policy block reason
- execution state, which should remain `not_executed` for report-only adapters

The adapter must not treat `decision.action` as permission to mutate the host.
For example, a `rollback_required` failure should become an incident note or
human escalation, not an automatic rollback.

## Safety Rules

- Redact before model input and before persisted adapter events.
- Keep raw logs, secrets, tokens, customer data, and full environment dumps out
  of examples and artifacts.
- Preserve the original CI job or platform failure status unless a separate
  reviewed policy and executor path explicitly authorizes a change.
- If Minerva is unavailable, report the adapter error and keep the original host
  failure.
- If policy blocks the decision, report the block reason and do not execute the
  proposed action.
- Do not require a hosted service, remote model, platform credentials, or
  network control plane for the minimum adapter path.

## Validation

Validate the example event wrappers with:

```bash
python3 -m unittest tests.test_adapter_event_examples
```

Adapter packages should add their own tests for host-specific event parsing,
redaction, invalid observation handling, policy-blocked decisions, and
Minerva-unavailable behavior.
