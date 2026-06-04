# Minerva Verify M0 Completion Record

Date: 2026-06-04

## Status

```text
Minerva Verify M0 is locally complete.
```

M0 means:

```text
Minerva can inspect a git diff, classify risk, generate merge evidence, execute
allowlisted verification checks, publish CI evidence, and evaluate the verifier
against a first local corpus.
```

## Completed Capabilities

### Local Merge Evidence

```bash
minerva verify --diff origin/main...HEAD --format markdown
minerva verify --diff origin/main...HEAD --format json
```

### Include Local New Files

```bash
minerva verify --diff HEAD --include-untracked --format markdown
```

### Exclude Unrelated Worktree Paths

```bash
minerva verify --diff HEAD --include-untracked --exclude ".tasks/T53.task.md" --format markdown
```

### Execute Safe Checks

```bash
minerva verify --diff HEAD --include-untracked --run --format markdown
```

Allowed checks:

```text
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
python3 -m minerva_kernel.verify_eval --format json
python3 -m minerva_kernel.eval_smoke
```

### Write Artifact

```bash
minerva verify --diff origin/main...HEAD --run --format json --output minerva-merge-evidence.json
```

### Path-Sensitive Policy Scan

`minerva verify --diff` now treats docs, tests, eval fixtures, and planning
files as example-text paths when scanning git-added lines for policy blockers.
Those files still count in changed-file evidence. Runtime paths still block
destructive command patterns and credential-like values detected by the
redaction engine.

### CI Evidence

The GitHub Actions smoke workflow now publishes:

- Minerva CI summary
- `minerva-ci-run.json`
- Minerva Merge Evidence summary
- `minerva-merge-evidence.json`

### Verify Eval

```bash
minerva verify-eval-report --format markdown
```

Current local fixture:

```text
25 verification cases
Useful Merge Evidence Rate: 25/25 (100.0%)
```

## M0 Boundaries

M0 does not:

- auto-merge PRs
- auto-edit files
- execute model-proposed commands
- run network/deployment checks by default
- claim full correctness
- replace human review

M0 does:

- expose verified evidence
- expose unverified risk
- execute a bounded allowlist
- block readiness when an allowlisted check fails
- preserve machine-readable evidence

## Current Known Limitations

- CI integration re-runs allowlisted checks after the existing smoke command.
- GitHub Actions status has not been verified on a pushed branch in this run.
- `ruff` is not available in the current local environment.
- T53 and M2 real-corpus work remain separate in-progress/uncommitted work.
- `ready` means local M0 evidence is sufficient for the configured checks, not
  formal correctness.

## Next Track

Recommended next track:

```text
Minerva Verify M1: PR review usefulness and real merge outcomes.
```

Candidate tasks:

- Create GitHub issues for T57-T63.
- Run the CI workflow on a pushed branch and attach artifacts.
- Add real PR review cases with human outcomes.
- Add repository profile support for required checks.
- Add run-record ingestion so CI smoke evidence can be reused instead of
  re-running checks.
- Add optional model-assisted risk hypotheses while keeping deterministic
  policy and evidence gates.
