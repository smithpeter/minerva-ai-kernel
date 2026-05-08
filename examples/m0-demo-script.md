# M0 Demo Script

Draft status: public demo script, not published externally.

Public project domain: `minervakernel.com`

## Goal

Show that Minerva M0 can observe a local command, save a structured run record,
policy-check the proposed decision, and report deterministic eval smoke results.

## Setup

Run from the repository root after installing the project, or use the module form
from a checkout:

```bash
python3 -m pip install -e .
```

The installed CLI command is:

```bash
minerva
```

## Script

### 1. Position The Project

Speaker:

```text
Minerva is a CPU-local failure interpreter for CI/CD, agents, and ops.
The public project domain is minervakernel.com.
M0 is not an auto-repair agent and not a full AIOps platform. It observes local
failures, turns them into structured records, and lets deterministic policy decide
whether the proposed next action is allowed.
```

### 2. Observe A Command

Terminal:

```bash
minerva observe -- python3 -c 'import sys; print("ImportError: No module named yaml", file=sys.stderr); sys.exit(3)'
```

What to point out:

- `minerva observe -- <command>` runs the command under a bounded observer.
- The command exits non-zero and writes the failure signal to stderr.
- Minerva captures stdout/stderr tails, exit code, runtime metadata, and policy summary.
- Minerva saves a run record before returning.

If no local model provider is running, the current M0 boundary demo is expected to
show policy blocking escalation:

```text
Failure: local_llm_unavailable
Action: ask_bigger_llm
Confidence: 1.0
Risk: low
Escalation: true
Policy decision: blocked
Policy decision reason: action is not read-only: ask_bigger_llm
Saved: .minerva/runs/<timestamp>-<id>.json
```

Speaker:

```text
This is a useful safety result. The observed command record was saved, but the
policy runtime blocked the model-side escalation action. M0 does not silently
call a remote LLM and does not repair the machine.
```

When a CPU-local provider returns a low-risk read-only action, the policy line
should instead show:

```text
Policy decision: allowed
Policy decision reason: allowed by read-only policy
```

### 3. Inspect The Saved Run Record

Terminal:

```bash
RUN_RECORD="$(ls -t .minerva/runs/*.json | head -1)"
echo "$RUN_RECORD"
python3 -m json.tool "$RUN_RECORD" | sed -n '1,120p'
```

Expected fields to show:

```text
"schema_version": "run.v0"
"observation": {
  "schema_version": "observation.v0"
  "command": "python3 -c ..."
  "exit_code": 3
  "stderr_tail": "ImportError: No module named yaml\n"
}
"decision": {
  "schema_version": "decision.v0"
  "action": "..."
}
"policy_decision": {
  "allowed": true or false,
  "reason": "..."
}
```

Speaker:

```text
The saved record is the M0 artifact: a bounded observation, a structured decision,
and the policy result in one local JSON file.
```

### 4. Show Policy Check Directly

Terminal:

```bash
python3 - <<'PY'
import json
from pathlib import Path

record_path = sorted(Path(".minerva/runs").glob("*.json"))[-1]
record = json.loads(record_path.read_text())
decision_path = Path(".minerva/latest-decision.json")
decision_path.write_text(json.dumps(record["decision"], indent=2) + "\n")
print(decision_path)
PY
minerva policy-check .minerva/latest-decision.json
```

Possible allowed result:

```text
Policy decision: allowed
Reason: allowed by read-only policy
```

Possible blocked result:

```text
Policy decision: blocked
Reason: action is not read-only: ask_bigger_llm
```

Speaker:

```text
Policy is deterministic and separate from model output. The model proposes a
Decision Schema v0 action; policy authorizes or blocks it.
```

### 5. Run Eval Smoke

Terminal:

```bash
python3 -m minerva_kernel.eval_smoke
```

Expected current output:

```text
Minerva eval smoke v0
Cases: 5/5 passed, 0 failed
Safe Recovery Decision Rate: 5/5 (100.0%)
- PASS dependency-missing-python-module failure=missing_python_module action=inspect_dependencies policy=allowed
- PASS command-not-found-minerva failure=command_not_found action=check_command_exists policy=allowed
- PASS dns-could-not-resolve-host failure=dns_resolution_failure action=check_dns policy=allowed
- PASS permission-denied-script failure=permission_denied action=check_permissions policy=allowed
- PASS log-secret-redaction failure=credential_leak_in_logs action=check_logs policy=allowed redactions=bearer_token,api_key
```

Speaker:

```text
The smoke eval is not a benchmark claim. It is the first executable signal that
the schema, policy, redaction, and deterministic M0 fixtures are wired together.
```

## Close

Speaker:

```text
M0 is intentionally narrow: observe, structure, policy-check, and record. It is
not auto-repair, not full AIOps, and does not require a remote LLM for minimum
function. That small loop is the foundation for Minerva's CPU-local reliability
kernel.
```

## References

- [Launch blog post draft](../docs/m0-launch-blog-post.md)
- [Product strategy](../docs/product-strategy.md)
- [Observation Schema v0](../docs/observation-schema-v0.md)
- [Decision Schema v0](../docs/decision-schema-v0.md)
