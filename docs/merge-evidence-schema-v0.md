# Merge Evidence Schema v0

Date: 2026-06-04

Status: draft

## Purpose

Merge Evidence Schema v0 defines the structured output for Minerva Verify.

The schema exists to make PR review evidence:

- reproducible
- concise
- machine-readable
- auditable
- useful to humans
- useful for future evals and training

## Object Shape

```json
{
  "schema_version": "merge_evidence.v0",
  "subject": {
    "type": "git_diff",
    "base": "origin/main",
    "head": "HEAD",
    "repository": "minerva-ai-kernel"
  },
  "summary": {
    "change_intent": "Add merge evidence reporting docs.",
    "changed_files": 3,
    "primary_areas": ["docs", "planning"],
    "risk_level": "low",
    "merge_readiness": "caution"
  },
  "verified": [
    {
      "kind": "compile",
      "command": "python3 -m compileall minerva_kernel",
      "status": "passed",
      "evidence": "command exited 0"
    }
  ],
  "unverified": [
    {
      "kind": "unit_tests",
      "reason": "full test suite was not run",
      "recommended_next_step": "python3 -m unittest discover -s tests"
    }
  ],
  "risks": [
    {
      "id": "docs_drift",
      "severity": "low",
      "description": "New strategy docs may drift from current roadmap if tasks are not created.",
      "mitigation": "Create local task cards and roadmap links."
    }
  ],
  "policy": {
    "dangerous_actions_detected": false,
    "writes_detected": true,
    "secret_access_detected": false,
    "decision": "allowed"
  },
  "recommended_next_steps": [
    "Create implementation task for minerva verify --diff."
  ],
  "audit": {
    "created_at": "2026-06-04T00:00:00Z",
    "generator": "minerva",
    "artifacts": []
  }
}
```

## Required Fields

```text
schema_version
subject
summary
verified
unverified
risks
policy
recommended_next_steps
audit
```

## Merge Readiness

```text
ready
caution
blocked
unknown
```

Rules:

- `ready`: main risk areas have relevant evidence and no blockers.
- `caution`: some evidence exists, but important risk remains unverified.
- `blocked`: required evidence failed or policy blocked the change.
- `unknown`: Minerva cannot classify readiness.

## Risk Levels

```text
low
medium
high
unknown
```

## Evidence Kinds

Initial evidence kinds:

```text
compile
unit_tests
integration_tests
eval
lint
typecheck
schema_check
policy_check
security_scan
dependency_check
runtime_smoke
manual_review
ci_log
artifact
```

## Risk Kinds

Initial risk kinds:

```text
missing_tests
test_failure
dangerous_action
secret_exposure
dependency_change
public_api_change
schema_change
runtime_behavior_change
performance_risk
security_boundary_change
migration_risk
docs_drift
unknown_impact
```

## Invariants

- A report must never say `ready` when required checks failed.
- A report must include at least one `unverified` item when full tests were not run.
- A report must distinguish evidence from inference.
- A report must not hide policy-blocked actions.
- A report must keep human-facing summary short.
- A report must preserve machine-readable evidence for later eval.

## First CLI Mapping

```bash
minerva verify --diff origin/main...HEAD --format json
minerva verify --diff origin/main...HEAD --format markdown
minerva verify --diff HEAD --include-untracked --format markdown
minerva verify --diff HEAD --include-untracked --exclude ".tasks/T53.task.md" --format markdown
minerva verify --diff HEAD --include-untracked --run --format markdown
minerva verify --diff HEAD --run --format json --output minerva-merge-evidence.json
minerva verify-eval-report --format markdown
```

`json` should emit `merge_evidence.v0`.

`markdown` should render a compact human report:

```text
Merge readiness: caution
Risk: low

Verified:
- compile passed

Unverified:
- full unit tests not run

Next step:
- run python3 -m unittest discover -s tests
```

## Eval Questions

Each merge evidence report should be evaluated against:

- Did it classify changed areas correctly?
- Did it identify the main missing evidence?
- Did it avoid unsupported confidence?
- Did it recommend a useful next verification step?
- Did it stay concise enough for review?
- Did the merge outcome later confirm or contradict the report?
