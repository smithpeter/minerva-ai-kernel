# Post-Metadata-Fix Local Release Dry-Run Evidence - 2026-05-08

## Summary

- Commit: `87dd7730a07f29c1b82de2ed937ad35c94db6e04`
- Repository root: `/Users/zouyongming/projects/minerva-ai-kernel`
- UTC timestamp: `2026-05-08T07:27:08Z`
- Host: `Darwin C02G75WJQ05N 25.2.0 ... RELEASE_ARM64_T8103 arm64`
- OS: `macOS 26.2`, build `25C56`
- System Python for required final gate: `Python 3.14.3` at `/opt/homebrew/bin/python3`
- Fresh install virtualenv Python: `Python 3.11.15` at `.venv-t36-py311/bin/python`
- Demo run record: `.minerva/runs/2026-05-08T072516Z-70f465d5.json`
- Redaction run record: `.minerva/runs/2026-05-08T072606Z-8a11d895.json`

The post-package-metadata-fix local release dry run passed. A fresh virtualenv
installed the project with the documented offline editable install command,
exposed the `minerva` console command, and ran `minerva doctor` successfully.
The run also covered `minerva observe --`, run record inspection,
`policy-check`, eval smoke, compile, unit tests, destructive-intent policy
blocking, and redaction before saved run records.

No release was published, no package was published, no external account was
created, no model was downloaded, no destructive command was executed, and no
remote LLM was required. With no local provider available, the M0 path failed
closed with a policy-blocked escalation decision.

## Machine Context

```bash
git rev-parse --show-toplevel
```

```text
/Users/zouyongming/projects/minerva-ai-kernel
```

```bash
git rev-parse HEAD
```

```text
87dd7730a07f29c1b82de2ed937ad35c94db6e04
```

```bash
python3 --version
```

```text
Python 3.14.3
```

```bash
which python3
```

```text
/opt/homebrew/bin/python3
```

```bash
sw_vers
```

```text
ProductName:		macOS
ProductVersion:		26.2
BuildVersion:		25C56
```

```bash
uname -a
```

```text
Darwin C02G75WJQ05N 25.2.0 Darwin Kernel Version 25.2.0: Tue Nov 18 21:09:55 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8103 arm64
```

## Fresh Editable Install And Console Command

```bash
python3.11 -m venv .venv-t36-py311
.venv-t36-py311/bin/python -m pip install --no-index --no-deps --no-build-isolation -e .
```

```text
Obtaining file:///Users/zouyongming/projects/minerva-ai-kernel
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Building wheels for collected packages: minerva-ai-kernel
  Building editable for minerva-ai-kernel (pyproject.toml): started
  Building editable for minerva-ai-kernel (pyproject.toml): finished with status 'done'
  Created wheel for minerva-ai-kernel: filename=minerva_ai_kernel-0.0.0-0.editable-py3-none-any.whl
Successfully built minerva-ai-kernel
Installing collected packages: minerva-ai-kernel
Successfully installed minerva-ai-kernel-0.0.0
```

```bash
. .venv-t36-py311/bin/activate && command -v minerva && minerva doctor
```

```text
/Users/zouyongming/projects/minerva-ai-kernel/.venv-t36-py311/bin/minerva
Minerva doctor: repository skeleton is ready.
```

```bash
.venv-t36-py311/bin/python - <<'PY'
import importlib.metadata as metadata

dist = metadata.distribution("minerva-ai-kernel")
print(dist.version)
print((dist.read_text("top_level.txt") or "").strip())
PY
```

```text
0.0.0
minerva_kernel
```

Interpreter note: this host's fresh Python 3.14 and Python 3.13 virtualenvs did
not seed `setuptools`, so the no-build-isolation install failed before project
metadata generation with `Cannot import 'setuptools.build_meta'`. The successful
dry-run install above used a fresh Python 3.11 virtualenv that included the
build backend locally and did not download dependencies.

## Observe Demo And Run Record Inspection

```bash
. .venv-t36-py311/bin/activate
set +e
minerva observe -- python3 -c 'import sys; print("ImportError: No module named yaml", file=sys.stderr); sys.exit(3)'
OBSERVE_STATUS=$?
set -e
printf 'OBSERVE_STATUS=%s\n' "$OBSERVE_STATUS"
```

```text
Failure: local_llm_unavailable
Action: ask_bigger_llm
Confidence: 1.0
Risk: low
Escalation: true
Policy decision: blocked
Policy decision reason: action is not read-only: ask_bigger_llm
Saved: .minerva/runs/2026-05-08T072516Z-70f465d5.json
OBSERVE_STATUS=2
```

```bash
RUN_RECORD=.minerva/runs/2026-05-08T072516Z-70f465d5.json
test -f "$RUN_RECORD"
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

```text
run record ok: .minerva/runs/2026-05-08T072516Z-70f465d5.json
```

The inspected run record had `schema_version` `run.v0`, observation schema
`observation.v0`, exit code `3`, the expected stderr tail, a `decision.v0`
decision, and a policy decision with both `allowed` and `reason` fields.

## Policy Check

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
printf 'POLICY_STATUS=%s\n' "$POLICY_STATUS"
```

```text
.minerva/latest-decision.json
Policy decision: blocked
Reason: action is not read-only: ask_bigger_llm
POLICY_STATUS=2
```

## Eval Smoke

```bash
. .venv-t36-py311/bin/activate
python3 -m minerva_kernel.eval_smoke
```

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

## Safety Checks

### Destructive Intent Block

The destructive string below was written only to structured policy-check input;
it was not executed.

```bash
python3 - <<'PY'
import json
from pathlib import Path

payload = {
    "action": "check_logs",
    "command": "rm -rf /tmp/minerva-release-dry-run",
}
path = Path("/tmp/minerva-blocked-decision-t36.json")
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(path)
PY

set +e
minerva policy-check /tmp/minerva-blocked-decision-t36.json
BLOCK_STATUS=$?
set -e
printf 'BLOCK_STATUS=%s\n' "$BLOCK_STATUS"
test "$BLOCK_STATUS" -eq 2
```

```text
/tmp/minerva-blocked-decision-t36.json
Policy decision: blocked
Reason: blocked destructive command attempt
BLOCK_STATUS=2
```

### Redaction Before Persisted Record

```bash
FAKE_TOKEN="abcdefghijklmnopqrstuvwxyz123456"
set +e
minerva observe -- python3 -c "print('Authorization: Bearer ${FAKE_TOKEN}')"
REDACTION_OBSERVE_STATUS=$?
set -e
printf 'REDACTION_OBSERVE_STATUS=%s\n' "$REDACTION_OBSERVE_STATUS"
REDACTION_RECORD="$(ls -t .minerva/runs/*.json | head -1)"
printf 'REDACTION_RECORD=%s\n' "$REDACTION_RECORD"
python3 - "$REDACTION_RECORD" "$FAKE_TOKEN" <<'PY'
import sys

record_text = open(sys.argv[1], encoding="utf-8").read()
secret = sys.argv[2]
assert secret not in record_text
assert "Bearer [REDACTED:bearer_token]" in record_text
print("redaction check passed:", sys.argv[1])
PY
```

```text
Failure: local_llm_unavailable
Action: ask_bigger_llm
Confidence: 1.0
Risk: low
Escalation: true
Policy decision: blocked
Policy decision reason: action is not read-only: ask_bigger_llm
Redaction summary: count=2 types=bearer_token
Saved: .minerva/runs/2026-05-08T072606Z-8a11d895.json
REDACTION_OBSERVE_STATUS=2
REDACTION_RECORD=.minerva/runs/2026-05-08T072606Z-8a11d895.json
redaction check passed: .minerva/runs/2026-05-08T072606Z-8a11d895.json
```

## Final Local Gate

```bash
python3 -m compileall minerva_kernel
```

```text
Listing 'minerva_kernel'...
```

```bash
python3 -m unittest discover -s tests
```

```text
Ran 83 tests in 4.373s

OK
```

```bash
python3 -m minerva_kernel.eval_smoke
```

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

## Remaining External Checks

- Remote GitHub Actions status was not verified by this local dry run.
- DNS, TLS, and HTTPS content for `minervakernel.com` were not verified by this
  local dry run.
- The no-build-isolation install path requires the fresh virtualenv to already
  provide the local build backend; Python 3.14 and Python 3.13 venvs on this
  host did not.
