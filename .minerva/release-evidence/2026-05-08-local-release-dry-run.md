# Local Release Dry-Run Evidence - 2026-05-08

## Summary

- Commit: `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7`
- Repository root: `/Users/zouyongming/projects/minerva-ai-kernel`
- UTC date: `2026-05-08T06:40:00Z`
- Host: `Darwin C02G75WJQ05N 25.2.0 ... RELEASE_ARM64_T8103 arm64`
- OS: `macOS 26.2`, build `25C56`
- System Python: `Python 3.14.3` at `/opt/homebrew/bin/python3`
- Virtualenv Python: `Python 3.11.14` at `.venv/bin/python3`
- Demo run record: `.minerva/runs/2026-05-08T064103Z-ba79c294.json`
- Redaction run record: `.minerva/runs/2026-05-08T064207Z-4d5cf3d7.json`

Local compile, unit tests, eval smoke, run-record inspection, policy checks, and
redaction checks passed. The install/smoke path exposed a release blocker:
editable install does not currently produce the `minerva` console command in a
fresh virtualenv because package metadata discovery fails.

No release was published, no external account was created, no destructive
command was executed, and no remote LLM was required. The local provider path
failed closed with a policy-blocked escalation decision.

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
ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7
```

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```

```text
2026-05-08T06:40:00Z
```

```bash
python3 --version && which python3
```

```text
Python 3.14.3
/opt/homebrew/bin/python3
```

```bash
. .venv/bin/activate && python3 --version && which python3
```

```text
Python 3.11.14
/Users/zouyongming/projects/minerva-ai-kernel/.venv/bin/python3
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

## Install And Console Smoke

```bash
python3 -m venv .venv
```

```text
```

```bash
. .venv/bin/activate && python3 -m pip install --no-deps -e .
```

```text
/Users/zouyongming/projects/minerva-ai-kernel/.venv/bin/python3: No module named pip
```

The virtualenv was bootstrapped with `ensurepip` so the install path could
continue:

```bash
. .venv/bin/activate && python3 -m ensurepip --upgrade
```

```text
Looking in links: /var/folders/1g/kplsdzrd7g972gvkq1sxtvxm0000gp/T/tmpf8_k4xhs
Processing /var/folders/1g/kplsdzrd7g972gvkq1sxtvxm0000gp/T/tmpf8_k4xhs/setuptools-79.0.1-py3-none-any.whl
Processing /var/folders/1g/kplsdzrd7g972gvkq1sxtvxm0000gp/T/tmpf8_k4xhs/pip-24.0-py3-none-any.whl
Installing collected packages: setuptools, pip
Successfully installed pip-24.0 setuptools-79.0.1
```

```bash
. .venv/bin/activate && python3 -m pip install --no-deps -e .
```

```text
WARNING: The directory '/Users/zouyongming/Library/Caches/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Obtaining file:///Users/zouyongming/projects/minerva-ai-kernel
  Installing build dependencies: started
  Installing build dependencies: finished with status 'error'
  error: subprocess-exited-with-error

  x pip subprocess to install build dependencies did not run successfully.
  | exit code: 1
  `-> [8 lines of output]
      WARNING: The directory '/Users/zouyongming/Library/Caches/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
      WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at 0x101852110>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known')': /simple/setuptools/
      WARNING: Retrying (Retry(total=3, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at 0x107895290>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known')': /simple/setuptools/
      WARNING: Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at 0x107895bd0>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known')': /simple/setuptools/
      WARNING: Retrying (Retry(total=1, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at 0x10788cf50>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known')': /simple/setuptools/
      WARNING: Retrying (Retry(total=0, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at 0x10788c750>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known')': /simple/setuptools/
      ERROR: Could not find a version that satisfies the requirement setuptools>=40.8.0 (from versions: none)
      ERROR: No matching distribution found for setuptools>=40.8.0
      [end of output]

  note: This error originates from a subprocess, and is likely not a problem with pip.
error: subprocess-exited-with-error

x pip subprocess to install build dependencies did not run successfully.
| exit code: 1
`-> See above for output.

note: This error originates from a subprocess, and is likely not a problem with pip.
```

The offline build isolation issue was bypassed with the already bootstrapped
virtualenv, but package discovery then failed:

```bash
. .venv/bin/activate && python3 -m pip install --no-deps --no-build-isolation -e .
```

```text
WARNING: The directory '/Users/zouyongming/Library/Caches/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Obtaining file:///Users/zouyongming/projects/minerva-ai-kernel
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'error'
  error: subprocess-exited-with-error

  x Preparing editable metadata (pyproject.toml) did not run successfully.
  | exit code: 1
  `-> [28 lines of output]
      /Users/zouyongming/projects/minerva-ai-kernel/.venv/lib/python3.11/site-packages/setuptools/config/_apply_pyprojecttoml.py:82: SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated
      !!

              ********************************************************************************
              Please use a simple string containing a SPDX expression for `project.license`. You can also use `project.license-files`. (Both options available on setuptools>=77.0.0).

              This deprecation is overdue, please update your project and remove deprecated
              calls to avoid build errors in the future.

              See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
              ********************************************************************************

      !!
        corresp(dist, value, root_dir)
      error: Multiple top-level packages discovered in a flat-layout: ['evals', 'models', 'policies', 'adapters', 'taxonomies', 'minerva_kernel'].

      To avoid accidental inclusion of unwanted files or directories,
      setuptools will not proceed with this build.

      If you are trying to create a single distribution with multiple packages
      on purpose, you should not rely on automatic discovery.
      Instead, consider the following options:

      1. set up custom discovery (`find` directive with `include` or `exclude`)
      2. use a `src-layout`
      3. explicitly set `py_modules` or `packages` with a list of names

      To find more information, look for "package discovery" on setuptools docs.
      [end of output]

  note: This error originates from a subprocess, and is likely not a problem with pip.
error: metadata-generation-failed

x Encountered error while generating package metadata.
`-> See above for output.

note: This is an issue with the package mentioned above, not pip.
hint: See above for details.
```

```bash
. .venv/bin/activate && command -v minerva && minerva doctor
```

```text
```

Exit status: `1`. Because the package install failed, no `minerva` console
script was available. The remaining CLI checks used the module entry point from
the checkout.

## Doctor

```bash
. .venv/bin/activate && python3 -m minerva_kernel.cli doctor
```

```text
Minerva doctor: repository skeleton is ready.
```

## Observe Demo Failure

```bash
. .venv/bin/activate
set +e
python3 -m minerva_kernel.cli observe -- python3 -c 'import sys; print("ImportError: No module named yaml", file=sys.stderr); sys.exit(3)'
OBSERVE_STATUS=$?
set -e
echo "OBSERVE_STATUS=$OBSERVE_STATUS"
if [ "$OBSERVE_STATUS" -ne 0 ] && [ "$OBSERVE_STATUS" -ne 2 ]; then
  exit "$OBSERVE_STATUS"
fi
```

```text
Failure: local_llm_unavailable
Action: ask_bigger_llm
Confidence: 1.0
Risk: low
Escalation: true
Policy decision: blocked
Policy decision reason: action is not read-only: ask_bigger_llm
Saved: .minerva/runs/2026-05-08T064103Z-ba79c294.json
OBSERVE_STATUS=2
```

## Run Record Inspection

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

```text
.minerva/runs/2026-05-08T064103Z-ba79c294.json
{
    "created_at": "2026-05-08T064103Z",
    "decision": {
        "action": "ask_bigger_llm",
        "confidence": 1.0,
        "escalate": true,
        "evidence": [
            "local LLM request failed"
        ],
        "failure": "local_llm_unavailable",
        "reason": "<urlopen error [Errno 1] Operation not permitted>",
        "risk": "low",
        "schema_version": "decision.v0"
    },
    "observation": {
        "command": "python3 -c 'import sys; print(\"ImportError: No module named yaml\", file=sys.stderr); sys.exit(3)'",
        "cwd": "/Users/zouyongming/projects/minerva-ai-kernel",
        "duration_ms": 13,
        "exit_code": 3,
        "policy_summary": "command attempted with 20s timeout; stdout/stderr tails limited to 12000 chars",
        "runtime": {
            "command_found": true,
            "machine": "arm64",
            "network_status": "unknown",
            "platform": "darwin",
            "platform_release": "25.2.0",
            "python": "3.11.14",
            "stderr_truncated": false,
            "stdout_truncated": false,
            "tail_chars": 12000,
            "timed_out": false,
            "timeout_seconds": 20.0
        },
        "schema_version": "observation.v0",
        "source": "local_shell",
        "stderr_tail": "ImportError: No module named yaml\n",
        "stdout_tail": ""
    },
    "policy_decision": {
        "allowed": false,
        "reason": "action is not read-only: ask_bigger_llm"
    },
    "schema_version": "run.v0"
}
run record ok: .minerva/runs/2026-05-08T064103Z-ba79c294.json
```

## Policy Check

This used `/tmp/minerva-t31-latest-decision.json` instead of
`.minerva/latest-decision.json` to keep generated dry-run state outside tracked
repo paths.

```bash
RUN_RECORD="$(ls -t .minerva/runs/*.json | head -1)"
python3 - "$RUN_RECORD" <<'PY'
import json
import sys
from pathlib import Path

with open(sys.argv[1], encoding="utf-8") as handle:
    record = json.load(handle)

decision_path = Path("/tmp/minerva-t31-latest-decision.json")
decision_path.write_text(json.dumps(record["decision"], indent=2) + "\n", encoding="utf-8")
print(decision_path)
PY

. .venv/bin/activate
set +e
python3 -m minerva_kernel.cli policy-check /tmp/minerva-t31-latest-decision.json
POLICY_STATUS=$?
set -e
echo "POLICY_STATUS=$POLICY_STATUS"
if [ "$POLICY_STATUS" -ne 0 ] && [ "$POLICY_STATUS" -ne 2 ]; then
  exit "$POLICY_STATUS"
fi
```

```text
/tmp/minerva-t31-latest-decision.json
Policy decision: blocked
Reason: action is not read-only: ask_bigger_llm
POLICY_STATUS=2
```

## Eval Smoke

```bash
. .venv/bin/activate && python3 -m minerva_kernel.eval_smoke
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

The destructive string below was not executed; it was only passed to
`policy-check` as structured input.

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

. .venv/bin/activate
set +e
python3 -m minerva_kernel.cli policy-check /tmp/minerva-blocked-decision.json
BLOCK_STATUS=$?
set -e
echo "BLOCK_STATUS=$BLOCK_STATUS"
test "$BLOCK_STATUS" -eq 2
```

```text
/tmp/minerva-blocked-decision.json
Policy decision: blocked
Reason: blocked destructive command attempt
BLOCK_STATUS=2
```

```bash
. .venv/bin/activate
FAKE_TOKEN="abcdefghijklmnopqrstuvwxyz123456"
set +e
python3 -m minerva_kernel.cli observe -- python3 -c "print('Authorization: Bearer ${FAKE_TOKEN}')"
REDACTION_OBSERVE_STATUS=$?
set -e
echo "REDACTION_OBSERVE_STATUS=$REDACTION_OBSERVE_STATUS"
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

```text
Failure: local_llm_unavailable
Action: ask_bigger_llm
Confidence: 1.0
Risk: low
Escalation: true
Policy decision: blocked
Policy decision reason: action is not read-only: ask_bigger_llm
Redaction summary: count=2 types=bearer_token
Saved: .minerva/runs/2026-05-08T064207Z-4d5cf3d7.json
REDACTION_OBSERVE_STATUS=2
redaction check passed: .minerva/runs/2026-05-08T064207Z-4d5cf3d7.json
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
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 3.814s

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

## Known Gaps And Blockers

- Fresh virtualenv creation under the available system Python produced a venv
  without `pip`; `python3 -m ensurepip --upgrade` repaired that local setup.
- `python3 -m pip install --no-deps -e .` attempted to fetch build
  dependencies under build isolation and failed in the restricted/offline
  environment.
- `python3 -m pip install --no-deps --no-build-isolation -e .` then failed
  package metadata generation because setuptools discovered multiple top-level
  packages in the flat layout: `evals`, `models`, `policies`, `adapters`,
  `taxonomies`, and `minerva_kernel`.
- Because editable install failed, the `minerva` console script was unavailable.
  CLI behavior was verified through `python3 -m minerva_kernel.cli ...` from the
  checkout.
- Remote GitHub Actions status, DNS, TLS, and public domain content were not
  verified by this local dry run.
