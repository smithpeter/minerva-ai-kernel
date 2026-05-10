# CI Log Analysis Example

Analyze an existing CI log without calling a hosted CI API:

```bash
minerva ci-analyze build.log --job-name unit-tests
```

The command:

- reads a bounded log tail from the local file
- constructs an `observation.v0` with `source: ci_log`
- redacts secrets before model input
- produces a `decision.v0`
- policy-checks the decision
- does not execute the selected action automatically

Example output:

```text
CI log: build.log
Observation source: ci_log
Failure: missing_python_module
Action: inspect_dependencies
Confidence: 0.9
Risk: low
Escalation: false
Policy decision: allowed
Policy decision reason: allowed by read-only policy
```

For large logs, keep the default bounded tail or pass a smaller limit:

```bash
minerva ci-analyze build.log --tail-chars 4000
```
