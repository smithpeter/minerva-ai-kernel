# Minerva Verify CI Handoff

Date: 2026-06-04

## Purpose

This handoff records the exact next step required to finish external M0
validation:

```text
push a clean Minerva Verify M0 branch and verify GitHub Actions artifacts.
```

Local M0 evidence is complete. The remaining evidence requires GitHub-side
execution.

## Clean Verify M0 Scope

Include:

```text
.github/workflows/ci-smoke.yml
.tasks/board.md
.tasks/T57.task.md
.tasks/T58.task.md
.tasks/T59.task.md
.tasks/T60.task.md
.tasks/T61.task.md
.tasks/T62.task.md
.tasks/T63.task.md
README.md
ROADMAP.md
docs/agent-kernel-abi-v0.md
docs/agent-os-bootstrap-strategy.md
docs/future-pc-agent-architecture-watchlist.md
docs/merge-evidence-schema-v0.md
docs/minerva-verify-ci-handoff.md
docs/minerva-verify-m0-completion.md
docs/minerva-verify-run-record-2026-06-04.md
docs/minerva-verify-strategy.md
evals/verify_cases_v0.json
minerva_kernel/cli.py
minerva_kernel/verify.py
minerva_kernel/verify_eval.py
tests/test_ci_workflow.py
tests/test_verify.py
tests/test_verify_eval.py
```

Exclude from the clean Verify M0 branch unless intentionally finishing T53/M2:

```text
.tasks/T53.task.md
eval/**
scripts/build_m2_real_corpus_report.py
tests/test_m2_real_corpus_report.py
```

Note:

```text
.tasks/board.md currently also contains a pre-existing T53 status change.
When preparing a clean branch, keep the T57-T63 rows but avoid unintentionally
claiming T53 completion.
```

## Local Evidence

Latest local checks:

```text
python3 -m unittest discover -s tests
157 tests passed, 2 skipped

python3 -m minerva_kernel.eval_smoke
5/5 passed

python3 -m minerva_kernel.verify_eval --format markdown
Useful Merge Evidence Rate: 25/25 (100.0%)

MINERVA_PROJECT_ROOT=/Users/zouyongming/projects/minerva-ai-kernel-verify-m0 bash scripts/check-project-boundary.sh
MINERVA_PROJECT_ROOT=/Users/zouyongming/projects/minerva-ai-kernel-verify-m0 bash scripts/check-contamination.sh
passed

python3 scripts/check-release-readiness.py --skip-external --install-backend auto
overall=pass
```

Clean local merge evidence command:

```bash
python3 -c 'from minerva_kernel.cli import main; main(["verify", "--diff", "HEAD", "--include-untracked", "--run", "--format", "json", "--output", "/tmp/minerva-verify-clean.json", "--exclude", ".tasks/T53.task.md", "--exclude", "eval/**", "--exclude", "scripts/build_m2_real_corpus_report.py", "--exclude", "tests/test_m2_real_corpus_report.py"])'
```

Current clean local summary:

```text
merge_readiness=caution
risk=medium
changed_files=26
remaining_unverified=GitHub Actions integration workflow execution
```

Policy scanning note:

```text
The clean branch includes path-sensitive policy text scanning. Git diff added
lines from docs, tests, eval fixtures, and planning files remain part of the
changed-file evidence, but example text there does not block merge readiness.
Runtime paths still block destructive command patterns and credential-like
values detected by the redaction engine.
```

## GitHub Evidence Required

After pushing a clean branch, verify:

- CI Smoke workflow starts.
- Existing Minerva CI summary appears in `$GITHUB_STEP_SUMMARY`.
- Minerva Merge Evidence summary appears in `$GITHUB_STEP_SUMMARY`.
- `minerva-ci-run` artifact uploads `minerva-ci-run.json`.
- `minerva-merge-evidence` artifact uploads `minerva-merge-evidence.json`.
- Workflow exit status remains tied to the observed smoke command, not AI
  confidence.

## Recommended Branch

```text
minerva-verify-m0
```

## Stop Conditions

Stop and ask before:

- pushing to GitHub
- creating public issues
- opening a PR
- merging to `main`
- deleting or rewriting unrelated T53/M2 work
