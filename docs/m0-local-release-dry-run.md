# M0 Local Release Dry Run

Use this checklist from a clean checkout before calling an M0 release candidate
ready. It verifies the local install path, `minerva doctor`, the observe demo,
saved run record inspection, eval smoke, and read-only safety boundaries.

Run every command from the repository root. The expected local artifacts are
`.venv/`, `.minerva/runs/*.json`, and `.minerva/latest-decision.json`; do not
commit those dry-run artifacts.

## Command Checklist

- Install the package locally.
- Run `minerva doctor`.
- Observe the demo failure and confirm a run record is saved.
- Inspect the latest `run.v0` record.
- Policy-check the saved decision.
- Run eval smoke.
- Check destructive-command blocking and redaction.
- Run the final compile and unit test gate.

## 1. Clean Checkout And Local Install

```bash
git clone https://github.com/smithpeter/minerva-ai-kernel.git
cd minerva-ai-kernel
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --no-index --no-deps --no-build-isolation -e .
```

Expected result:

- The `minerva` console command is available in the activated virtualenv.
- Setuptools installs only the intended `minerva_kernel` Python package; data
  directories such as `evals`, `models`, `policies`, `adapters`, and
  `taxonomies` are not treated as top-level import packages.
- Local artifact: `.venv/`.
- No remote LLM, cloud account, publish token, or deployment target is required.

## 2. Doctor Check

```bash
minerva doctor
```

Expected output:

```text
Minerva doctor: repository skeleton is ready.
```

Expected artifacts:

- No run record is created by `doctor`.

## 3. Observe Demo Failure

```bash
set +e
minerva observe -- python3 -c 'import sys; print("ImportError: No module named yaml", file=sys.stderr); sys.exit(3)'
OBSERVE_STATUS=$?
set -e
if [ "$OBSERVE_STATUS" -ne 0 ] && [ "$OBSERVE_STATUS" -ne 2 ]; then
  exit "$OBSERVE_STATUS"
fi
```

Expected output includes the diagnosis fields and a saved run record path:

```text
Failure: ...
Action: ...
Confidence: ...
Risk: ...
Escalation: ...
Policy decision: allowed or blocked
Policy decision reason: ...
Saved: .minerva/runs/<timestamp>-<id>.json
```

If no local OpenAI-compatible provider is running, the M0 boundary path is
expected to be policy-blocked rather than falling back to a remote LLM:

```text
Failure: local_llm_unavailable
Action: ask_bigger_llm
Policy decision: blocked
Policy decision reason: action is not read-only: ask_bigger_llm
```

Expected artifacts:

- `.minerva/runs/<timestamp>-<id>.json`
- The saved record contains the demo command, exit code `3`, stderr tail
  `ImportError: No module named yaml`, the structured decision, and the policy
  result.

## 4. Inspect The Run Record

```bash
RUN_RECORD="$(ls -t .minerva/runs/*.json | head -1)"
test -f "$RUN_RECORD"
echo "$RUN_RECORD"
python3 -m json.tool "$RUN_RECORD" | sed -n '1,160p'
python3 - "$RUN_RECORD" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    record = json.load(handle)

assert record["schema_version"] == "run.v0"
assert record["observation"]["schema_version"] == "observation.v0"
assert record["observation"]["exit_code"] == 3
assert "ImportError: No module named yaml" in record["observation"]["stderr_tail"]
assert record["decision"]["schema_version"] == "decision.v0"
assert "allowed" in record["policy_decision"]
assert "reason" in record["policy_decision"]
print("run record ok:", sys.argv[1])
PY
```

Expected output:

```text
run record ok: .minerva/runs/<timestamp>-<id>.json
```

Expected artifacts:

- The same `.minerva/runs/<timestamp>-<id>.json` inspected above.

## 5. Policy-Check The Saved Decision

```bash
python3 - "$RUN_RECORD" <<'PY'
import json
import sys
from pathlib import Path

with open(sys.argv[1], encoding="utf-8") as handle:
    record = json.load(handle)

decision_path = Path(".minerva/latest-decision.json")
decision_path.write_text(json.dumps(record["decision"], indent=2) + "\n", encoding="utf-8")
print(decision_path)
PY

set +e
minerva policy-check .minerva/latest-decision.json
POLICY_STATUS=$?
set -e
if [ "$POLICY_STATUS" -ne 0 ] && [ "$POLICY_STATUS" -ne 2 ]; then
  exit "$POLICY_STATUS"
fi
```

Expected output is one of these deterministic policy states:

```text
Policy decision: allowed
Reason: allowed by read-only policy
```

```text
Policy decision: blocked
Reason: action is not read-only: ask_bigger_llm
```

Expected artifacts:

- `.minerva/latest-decision.json`
- No tool execution is performed by `policy-check`; it validates the decision
  payload only.

## 6. Eval Smoke

```bash
python3 -m minerva_kernel.eval_smoke
```

Expected output:

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

Expected artifacts:

- No required persistent artifact. The command prints the deterministic smoke
  result for the packaged M0 cases.

## 7. Safety Checks

Confirm destructive shell intent is blocked by the read-only policy:

```bash
python3 - <<'PY'
import json
from pathlib import Path

payload = {
    "action": "check_logs",
    "command": "rm -rf /tmp/minerva-release-dry-run",
}
path = Path("/tmp/minerva-blocked-decision.json")
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(path)
PY

set +e
minerva policy-check /tmp/minerva-blocked-decision.json
BLOCK_STATUS=$?
set -e
test "$BLOCK_STATUS" -eq 2
```

Expected output:

```text
Policy decision: blocked
Reason: blocked destructive command attempt
```

Confirm known token-like values are redacted before saved records are written:

```bash
FAKE_TOKEN="abcdefghijklmnopqrstuvwxyz123456"
set +e
minerva observe -- python3 -c "print('Authorization: Bearer ${FAKE_TOKEN}')"
REDACTION_OBSERVE_STATUS=$?
set -e
if [ "$REDACTION_OBSERVE_STATUS" -ne 0 ] && [ "$REDACTION_OBSERVE_STATUS" -ne 2 ]; then
  exit "$REDACTION_OBSERVE_STATUS"
fi

REDACTION_RECORD="$(ls -t .minerva/runs/*.json | head -1)"
python3 - "$REDACTION_RECORD" "$FAKE_TOKEN" <<'PY'
import sys

record_text = open(sys.argv[1], encoding="utf-8").read()
secret = sys.argv[2]
assert secret not in record_text
assert "Bearer [REDACTED:bearer_token]" in record_text
print("redaction check passed:", sys.argv[1])
PY
```

Expected output includes:

```text
Redaction summary: count=... types=bearer_token
redaction check passed: .minerva/runs/<timestamp>-<id>.json
```

Expected artifacts:

- `/tmp/minerva-blocked-decision.json`
- A second `.minerva/runs/<timestamp>-<id>.json` containing
  `Bearer [REDACTED:bearer_token]`, not the fake token value.

## 8. Final Local Gate

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
python3 -m minerva_kernel.eval_smoke
```

Expected result:

- `compileall` exits `0`.
- Unit tests exit `0`.
- Eval smoke reports `Cases: 5/5 passed, 0 failed`.

## Completion Record

Record these values in the release decision or PR before marking M0 ready:

- Commit SHA used for the dry run.
- Python version and operating system.
- `RUN_RECORD` path from the observe demo.
- `REDACTION_RECORD` path from the redaction safety check.
- Exact outputs or CI links for compile, unit tests, and eval smoke.
- Confirmation that no release was published, no hosted service was deployed,
  and no remote LLM was required for the minimum M0 path.

## Recorded Evidence

- [2026-05-08 local release dry-run evidence](../.minerva/release-evidence/2026-05-08-local-release-dry-run.md)
  for commit `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7`.
