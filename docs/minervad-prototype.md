# Minervad Prototype

`minervad` is a local-only prototype health server for future daemon work.

Run it explicitly:

```bash
minerva minervad --host 127.0.0.1 --port 8765
```

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

Boundaries:

- It is not started by `minerva observe`.
- It is not started by CI.
- It is not started by the AI-team timer.
- It uses only Python standard-library HTTP serving.
- The default host is `127.0.0.1`; do not bind a remote interface without a
  separate reviewed deployment plan.
