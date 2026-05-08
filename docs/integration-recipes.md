# Integration Recipes

Date: 2026-05-08

These recipes show how to use Minerva as a local diagnostic layer for CI,
Python SDK callers, and agent tool failures. Each recipe preserves the current
defaults:

- observations are redacted before model input and persisted output
- decisions pass through the read-only policy gate
- proposed actions are advisory and are not executed automatically
- raw logs, credentials, and full tool inputs stay outside Minerva artifacts

## Recipe 1: GitHub Actions CI Diagnostics

Use this recipe when a CI job should keep failing or passing based on the
observed command, while Minerva publishes bounded diagnostic evidence.

Required inputs:

- a checked out repository with Minerva installed from the current checkout
- the command to observe, for example `python3 -m unittest discover -s tests`
- optional artifact upload permission from the standard `actions/upload-artifact`
  action

Copyable workflow step:

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

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Minerva
        run: python3 -m pip install --no-deps .

      - name: Observe tests with Minerva
        shell: bash
        run: |
          set +e
          minerva observe -- bash -c 'python3 -m compileall minerva_kernel && python3 -m unittest discover -s tests'
          minerva_status=$?
          set -e

          run_record="$(ls -t .minerva/runs/*.json 2>/dev/null | head -n 1 || true)"
          if [ -z "$run_record" ]; then
            {
              echo "# Minerva CI Summary"
              echo ""
              echo "Minerva did not write a run record."
            } >> "$GITHUB_STEP_SUMMARY"
            exit "$minerva_status"
          fi

          minerva render-ci-summary "$run_record" >> "$GITHUB_STEP_SUMMARY"
          minerva render-ci-artifact "$run_record" > minerva-ci-run.json

          observed_status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["observation"]["exit_code"])' "$run_record")"
          exit "$observed_status"

      - name: Upload Minerva CI artifact
        if: ${{ always() && hashFiles('minerva-ci-run.json') != '' }}
        uses: actions/upload-artifact@v4
        with:
          name: minerva-ci-run
          path: minerva-ci-run.json
          if-no-files-found: error
          retention-days: 7
```

Local dry run:

```bash
python3 -m pip install --no-deps .
minerva observe -- bash -c 'python3 -m compileall minerva_kernel && python3 -m unittest discover -s tests'
run_record="$(ls -t .minerva/runs/*.json | head -n 1)"
minerva render-ci-summary "$run_record"
minerva render-ci-artifact "$run_record" > minerva-ci-run.json
```

Outputs and diagnostic retrieval:

- CLI output shows the proposed failure label, diagnostic action, confidence,
  risk, escalation flag, policy decision, policy reason, redaction summary, and
  saved run record path.
- `.minerva/runs/<timestamp>-<id>.json` stores the redacted local `run.v0`
  record.
- `$GITHUB_STEP_SUMMARY` receives a compact markdown summary with the observed
  command, exit code, decision, policy gate, and bounded stdout/stderr excerpts.
- `minerva-ci-run.json` stores the normalized `minerva_ci_run.v0` artifact for
  download from the workflow run's Artifacts section.

Safety boundaries:

- The workflow exits with the observed command's exit code so Minerva cannot
  mask the CI gate.
- `render-ci-summary` and `render-ci-artifact` are local renderers. They do not
  call the GitHub API and do not require GitHub API credentials.
- The artifact records `auto_repair: false`, `policy_gated: true`,
  `model_input_redacted: true`, and `artifact_redacted: true`.
- Upload only `minerva-ci-run.json` and the markdown summary. Do not upload full
  raw logs, environment dumps, credential files, or unredacted provider prompts.

Expected failure modes:

- If the observed command fails, the CI job fails with that command's exit code
  after writing diagnostic evidence.
- If Minerva cannot reach a local model provider, the default provider records a
  `local_llm_unavailable` decision that policy blocks as escalation; the record
  is still useful as local diagnostic evidence.
- If the observed command times out, the observation records exit code `124` and
  `runtime.timed_out: true`.
- If Minerva cannot write a run record, the step writes a short summary and exits
  with `minerva_status`.

## Recipe 2: Direct Python SDK Usage

Use this recipe when an application already has a structured failure event and
wants a policy-gated Minerva decision without shelling out to the CLI.

Required inputs:

- an `Observation` or an `observation.v0` JSON file
- bounded stdout and stderr tails, not full logs
- a provider, such as `MockModelProvider` for tests or the default local
  OpenAI-compatible provider for runtime use

Run the bundled example:

```bash
python3 examples/minimal_sdk_decision.py
```

Minimal SDK snippet:

```python
from minerva_kernel import Decision, Minerva, MockModelProvider, Observation

observation = Observation(
    command="python3 -m unittest discover -s tests",
    cwd="/workspace/example-project",
    exit_code=1,
    stdout_tail="",
    stderr_tail="ModuleNotFoundError: No module named 'example_package'",
    duration_ms=742,
    source="sdk_recipe",
    policy_summary=(
        "local SDK observation; bounded stderr only; no secrets or external "
        "service credentials"
    ),
    runtime={
        "python": "3.12",
        "platform": "linux",
        "network_status": "not_required",
    },
)

kernel = Minerva(
    provider=MockModelProvider(
        Decision(
            failure="missing_python_dependency",
            action="inspect_dependencies",
            confidence=0.86,
            risk="low",
            escalate=False,
            evidence=["stderr contains ModuleNotFoundError"],
            reason="Inspect dependency metadata before retrying the test run.",
        )
    )
)

diagnosis = kernel.decide(observation)

print(diagnosis.decision.to_dict())
print(
    {
        "allowed": diagnosis.policy_decision.allowed,
        "reason": diagnosis.policy_decision.reason,
    }
)
```

File-based SDK usage:

```python
from minerva_kernel import Minerva

diagnosis = Minerva().decide_file("observation.json")
if diagnosis.policy_decision.allowed:
    print(diagnosis.decision.action)
else:
    print(f"blocked: {diagnosis.policy_decision.reason}")
```

Outputs and diagnostic retrieval:

- `diagnosis.decision` is a redacted `decision.v0` object with `failure`,
  `action`, `confidence`, `risk`, `escalate`, `evidence`, and optional `reason`.
- `diagnosis.policy_decision` says whether the read-only policy accepted the
  decision and why.
- `diagnosis.redactions` summarizes any redactions merged from the observation
  and decision.
- The SDK does not write `.minerva/runs/` by itself. Use the CLI or
  `minerva_kernel.observe.save_run_record` only when the application explicitly
  wants a local persisted record.

Safety boundaries:

- `Observation.to_dict()` redacts sensitive text before serialization.
- `Minerva.decide()` redacts the observation before building provider prompts.
- `ModelProvider.propose()` redacts messages again before provider calls and
  redacts provider decisions before returning them.
- Treat `diagnosis.decision.action` as advisory. The SDK does not execute the
  action.
- Trust only decisions with `diagnosis.policy_decision.allowed is True`; blocked
  decisions are audit evidence.

Expected failure modes:

- Invalid observation JSON raises `ValueError`, for example for an unsupported
  `schema_version` or missing required string.
- A local provider outage becomes a policy-blocked escalation decision from the
  default local provider.
- Unknown action labels, write-capable actions, medium or high risk, low
  confidence, and escalation requests are policy-blocked.

## Recipe 3: Agent Tool-Failure Loop

Use this recipe when an agent catches a failed tool call and needs a local,
policy-gated diagnostic suggestion before deciding how to continue.

Required inputs:

- tool name and a redacted tool call identifier
- input key names only, not raw input values
- bounded error text and elapsed time
- adapter policy summary that states the agent will not auto-execute Minerva
  actions

Run the bundled example:

```bash
python3 examples/agent_tool_failure.py
```

Minimal loop:

```python
import time

from minerva_kernel import Decision, Minerva, MockModelProvider, Observation


class ToolCallError(RuntimeError):
    pass


def run_agent_tool(args: dict[str, str]) -> str:
    raise ToolCallError("command not found: rg")


started = time.monotonic()
try:
    result = run_agent_tool({"query": "missing dependency failure"})
except ToolCallError as exc:
    observation = Observation(
        command="agent_tool:local_repo_search",
        cwd="/workspace/example-agent",
        exit_code=None,
        stdout_tail="",
        stderr_tail=f"{exc.__class__.__name__}: {exc}",
        duration_ms=max(0, int((time.monotonic() - started) * 1000)),
        source="agent_tool_recipe",
        policy_summary=(
            "agent caught a failed local tool call; inputs are represented by "
            "key names only; Minerva must not execute recovery automatically"
        ),
        runtime={
            "agent": {
                "framework": "local_example",
                "tool_name": "local_repo_search",
                "tool_call_id": "local-redacted-tool-call",
                "input_keys": ["query"],
            },
            "network_status": "not_required",
        },
    )
else:
    observation = None

if observation is not None:
    kernel = Minerva(
        provider=MockModelProvider(
            Decision(
                failure="agent_tool_command_missing",
                action="check_command_exists",
                confidence=0.9,
                risk="low",
                escalate=False,
                evidence=["tool error reports command not found"],
                reason="Confirm the local search command exists before retrying.",
            )
        )
    )
    diagnosis = kernel.decide(observation)

    if diagnosis.policy_decision.allowed:
        next_step = {
            "state": "diagnostic_ready",
            "action": diagnosis.decision.action,
            "reason": diagnosis.decision.reason,
        }
    else:
        next_step = {
            "state": "diagnostic_blocked",
            "reason": diagnosis.policy_decision.reason,
        }
```

Outputs and diagnostic retrieval:

- The adapter can log `observation.to_dict()` and `diagnosis.decision.to_dict()`
  after redaction.
- `runtime.agent.tool_name`, `tool_call_id`, and `input_keys` give enough
  routing context to debug the tool failure without persisting raw tool inputs.
- `diagnosis.policy_decision.reason` explains why the action can be presented to
  the agent loop or why it must remain audit-only.
- The bundled example prints JSON with the observation, decision, policy result,
  and an explicit `execution.state: not_executed` marker.

Safety boundaries:

- The agent adapter catches failures and creates observations; Minerva does not
  call tools directly.
- The agent must not pass raw prompts, secrets, file contents, cookies, tokens,
  or full tool arguments into `runtime`.
- Allowed Minerva actions are still diagnostic labels. The adapter decides how
  to route them and must keep any actual tool execution behind its own policy.
- Escalation actions such as `ask_bigger_llm` are blocked by the default
  read-only policy.

Expected failure modes:

- If the tool succeeds, skip Minerva and continue the normal agent path.
- If the tool error contains a secret-like value, Minerva redaction replaces the
  value with a `[REDACTED:<type>]` marker in serialized output.
- If the provider proposes an unsafe, unknown, low-confidence, or escalating
  action, `diagnosis.policy_decision.allowed` is `False`.
- If the adapter gives Minerva an invalid observation, construction or
  deserialization raises `ValueError`; handle that as an adapter bug, not as a
  recovery instruction.
