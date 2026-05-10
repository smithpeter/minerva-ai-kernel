# Minervad Prototype

`minervad` is a local-only prototype health server for future daemon work.

Run it explicitly:

```bash
minerva minervad --host 127.0.0.1 --port 8765
```

Run the local smoke check without leaving a daemon running:

```bash
python3 scripts/minervad-diagnose-smoke.py
```

The smoke script starts `minervad` on a random localhost port, checks
`/health`, posts a bounded `observation.v0` to `/diagnose`, verifies policy
status, verifies `execution.state=not_executed`, and shuts the server down.

Health endpoint:

```bash
curl http://127.0.0.1:8765/health
```

Response shape:

```json
{
  "mode": "prototype",
  "schema_version": "minervad_health.v0",
  "service": "minervad",
  "status": "ok"
}
```

Diagnosis endpoint:

```bash
curl -X POST http://127.0.0.1:8765/diagnose \
  -H 'Content-Type: application/json' \
  --data @observation.json
```

Request shape: a bounded `observation.v0` JSON object.

Response shape:

```json
{
  "decision": {
    "action": "inspect_dependencies",
    "confidence": 0.89,
    "escalate": false,
    "evidence": ["observation contains a missing dependency signal"],
    "failure": "missing_dependency",
    "reason": "Inspect dependency declarations and the active runtime environment.",
    "risk": "low",
    "schema_version": "decision.v0"
  },
  "execution": {
    "reason": "minervad diagnose is read-only",
    "state": "not_executed"
  },
  "policy_decision": {
    "allowed": true,
    "reason": "allowed by read-only policy"
  },
  "schema_version": "minervad_diagnosis.v0"
}
```

Error handling:

- Invalid JSON returns HTTP 400 with `error=invalid_json`.
- Invalid `observation.v0` payloads return HTTP 400 with
  `error=invalid_observation`.
- `GET /diagnose` returns HTTP 405.
- Request bodies above 1,000,000 bytes return HTTP 413.

Boundaries:

- It is not started by `minerva observe`.
- It is not started by CI.
- It is not started by the AI-team timer.
- It uses only Python standard-library HTTP serving.
- `POST /diagnose` only diagnoses and policy-gates; it never executes actions.
- The default host is `127.0.0.1`; do not bind a remote interface without a
  separate reviewed deployment plan.
