# Execute Action Demo

This demo shows Minerva's explicit read-only follow-up path. `minerva observe`
and the SDK do not execute diagnostic actions automatically. A caller must pass
a decision file to `minerva execute-action`.

Create a source observation:

```bash
cat > observation.json <<'JSON'
{
  "schema_version": "observation.v0",
  "command": "python -m pytest",
  "cwd": ".",
  "exit_code": 1,
  "stdout_tail": "",
  "stderr_tail": "ModuleNotFoundError: No module named yaml",
  "duration_ms": 120,
  "source": "demo",
  "policy_summary": "bounded demo observation"
}
JSON
```

Create an allowed read-only decision:

```bash
cat > decision.json <<'JSON'
{
  "schema_version": "decision.v0",
  "failure": "missing_dependency",
  "action": "inspect_dependencies",
  "confidence": 0.91,
  "risk": "low",
  "escalate": false,
  "evidence": ["stderr contains ModuleNotFoundError"]
}
JSON
```

Run the explicit executor:

```bash
minerva execute-action decision.json --observation observation.json --cwd .
```

Expected shape:

```json
{
  "schema_version": "observation.v0",
  "source": "kernel_executor",
  "command": "executor:inspect_dependencies",
  "policy_summary": "explicit read-only executor; no shell commands or writes"
}
```

Policy-blocked decisions are returned as executor observations and exit with
status `2`:

```bash
cat > blocked-decision.json <<'JSON'
{
  "schema_version": "decision.v0",
  "failure": "needs_operator",
  "action": "ask_user",
  "confidence": 0.91,
  "risk": "low",
  "escalate": true,
  "evidence": ["operator needed"]
}
JSON

minerva execute-action blocked-decision.json --cwd .
```

The executor remains diagnostic only: it does not run shell commands, write
files, install packages, retry the failed command, or repair the system.
