# sample-consumer — How to use Minerva from another repo

This directory is a **drop-in template** for any GitHub repo that
wants Minerva to diagnose CI failures. Copy the files in this
directory to the root of your own repo and you get:

- a `failing-build.sh` script that fails with a typical
  `ModuleNotFoundError`
- a `.github/workflows/ci.yml` that runs it and intentionally
  succeeds-or-fails based on the build
- a `.github/workflows/minerva-diagnose.yml` that, when the CI
  workflow fails, captures the build log and runs Minerva's
  composite GitHub Action against it

The Minerva step is **diagnostic only**. It writes a markdown summary
to `$GITHUB_STEP_SUMMARY` and uploads a JSON artifact. It does not
install packages, edit files, retry the build, or open PRs.

## Layout

```
sample-consumer/
├── README.md                          (this file)
├── failing-build.sh                   (the build script under CI)
├── app/
│   └── sample_app.py                  (the Python file the build runs)
└── .github/
    └── workflows/
        ├── ci.yml                     (runs the build)
        └── minerva-diagnose.yml       (runs Minerva when ci fails)
```

## Copy these files into your own repo

```bash
# from your own repo root, with minerva-ai-kernel checked out alongside
cp ../minerva-ai-kernel/examples/sample-consumer/failing-build.sh .
mkdir -p app .github/workflows
cp ../minerva-ai-kernel/examples/sample-consumer/app/sample_app.py app/
cp ../minerva-ai-kernel/examples/sample-consumer/.github/workflows/ci.yml .github/workflows/
cp ../minerva-ai-kernel/examples/sample-consumer/.github/workflows/minerva-diagnose.yml .github/workflows/
```

Then edit `.github/workflows/minerva-diagnose.yml` to reference
Minerva at the ref you want — typically a release tag or
`@main`.

## What you should see in Actions

When the CI workflow fails (it will, by design — `sample_app.py`
imports a deliberately-nonexistent module), the `minerva-diagnose`
workflow runs and the run page summary shows something like:

```
## Minerva Failure Diagnosis
CI log: build.log
Observation source: ci_log
Failure: missing_dependency
Action: inspect_dependencies
Risk: low
Policy decision: allowed
Policy decision reason: allowed by read-only policy
```

That is the entire integration. No agent, no auto-fix, no remote
LLM.

## What this dogfoods

This template exercises:

1. The composite `action.yml` at the root of the Minerva repo.
2. `minerva ci-analyze`'s log-tail capture and redaction.
3. The CPU-local baseline interpreter on a real CI log.
4. The Markdown summary writer for GitHub Step Summary.

It does **not** dogfood `minerva observe -- <command>` (which
needs to wrap the command itself) or the optional local model
provider path. Those are separate templates that may be added
later.
