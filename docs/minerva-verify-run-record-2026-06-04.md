# Minerva Verify Run Record

Date: 2026-06-04

Purpose:

```text
Record the first strategy-level Minerva Verify validation run after adding the
verification-kernel direction and Merge Evidence Schema v0 draft.
```

## Change Summary

Added:

- `minerva_kernel/verify.py`
- `minerva_kernel/verify_eval.py`
- `docs/minerva-verify-strategy.md`
- `docs/merge-evidence-schema-v0.md`
- `docs/agent-os-bootstrap-strategy.md`
- `docs/agent-kernel-abi-v0.md`
- `docs/future-pc-agent-architecture-watchlist.md`
- `evals/verify_cases_v0.json`
- `.tasks/T57.task.md`
- `.tasks/T58.task.md`
- `.tasks/T59.task.md`
- `.tasks/T60.task.md`
- `.tasks/T61.task.md`
- `.tasks/T62.task.md`
- `.tasks/T63.task.md`
- `tests/test_verify.py`
- `tests/test_verify_eval.py`

Updated:

- `README.md`
- `ROADMAP.md`
- `.tasks/board.md`
- `.github/workflows/ci-smoke.yml`
- `minerva_kernel/cli.py`
- `tests/test_ci_workflow.py`

Note:

```text
.tasks/T53.task.md`, `eval/`, `scripts/build_m2_real_corpus_report.py`, and
`tests/test_m2_real_corpus_report.py` were already present as separate
uncommitted work and were not part of this strategy change.
```

## Verification Evidence

### Compile Check

Command:

```bash
python3 -m compileall minerva_kernel
```

Result:

```text
passed
```

### Unit Tests

Command:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
157 tests passed, 2 skipped
```

### Eval Smoke

Command:

```bash
python3 -m minerva_kernel.eval_smoke
```

Result:

```text
5/5 cases passed
Safe Recovery Decision Rate: 100.0%
```

### Project Boundary Check

Command:

```bash
MINERVA_PROJECT_ROOT=/Users/zouyongming/projects/minerva-ai-kernel-verify-m0 bash scripts/check-project-boundary.sh
```

Result:

```text
passed
```

### Contamination Check

Command:

```bash
MINERVA_PROJECT_ROOT=/Users/zouyongming/projects/minerva-ai-kernel-verify-m0 bash scripts/check-contamination.sh
```

Result:

```text
passed
```

### Offline Release Readiness

Command:

```bash
python3 scripts/check-release-readiness.py --skip-external --install-backend auto
```

Result:

```text
overall=pass
```

Skipped by design:

- GitHub Actions status
- public DNS
- public TLS
- public HTTPS
- public content review

Reason:

```text
This was an offline local validation run.
```

### Verify Eval

Command:

```bash
python3 -m minerva_kernel.verify_eval --format markdown
```

Result:

```text
Useful Merge Evidence Rate: 25/25 (100.0%)
```

### Merge Evidence Prototype

Command:

```bash
python3 -c 'from minerva_kernel.cli import main; main(["verify", "--diff", "HEAD", "--format", "markdown", "--include-untracked", "--run"])'
```

Result:

```text
merge_readiness=caution
risk=medium
changed_files=26
primary_areas=ci, docs, eval, planning, runtime, schema, tests
allowlisted checks: compile, unit_tests, verify_eval, runtime_smoke all passed
remaining unverified: GitHub Actions integration workflow execution
```

Policy scanning follow-up:

```text
The first commit-range self-check correctly exposed a verifier false positive:
fixture and documentation examples containing dangerous strings were being
treated as real merge blockers. The final branch fixes this with
path-sensitive git-added-line scanning. Direct policy/eval cases still block
dangerous commands and credential-like additions, while docs, tests, eval
fixtures, and planning files are treated as example text for merge policy.
```

## Merge Evidence Draft

```json
{
  "schema_version": "merge_evidence.v0",
  "summary": {
    "change_intent": "Add Minerva Verify strategic direction, CLI prototype, CI artifact, first eval corpus, run mode, and M0 completion record.",
    "primary_areas": ["ci", "docs", "eval", "planning", "runtime", "schema", "tests"],
    "risk_level": "medium",
    "merge_readiness": "caution"
  },
  "verified": [
    "compile check passed",
    "unit tests passed",
    "eval smoke passed",
    "verify eval passed",
    "merge evidence prototype rendered and allowlisted checks passed",
    "project boundary check passed",
    "contamination check passed",
    "offline release readiness passed"
  ],
  "unverified": [
    "GitHub Actions status was skipped",
    "public domain checks were skipped",
    "T53/eval uncommitted work was not reviewed as part of this strategy change"
  ],
  "recommended_next_steps": [
    "Create GitHub issues for T57-T63",
    "Run the GitHub Actions workflow on a pushed branch"
  ]
}
```
