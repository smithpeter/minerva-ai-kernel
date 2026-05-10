# Five-Minute Demo

This demo shows Minerva's narrow value without a remote model, hosted service,
GPU, or auto-repair.

## 1. Install From The Checkout

```bash
python3 -m pip install --no-deps .
```

## 2. Diagnose A CI-Style Log

```bash
minerva ci-analyze examples/logs/missing-dependency.log --job-name demo
```

Expected shape:

```text
CI log: examples/logs/missing-dependency.log
Observation source: ci_log
Failure: missing_dependency
Action: inspect_dependencies
Risk: low
Policy decision: allowed
Policy decision reason: allowed by read-only policy
```

The output is advisory. Minerva does not install the missing package, edit
files, or retry the job.

## 3. Run The Local Eval Smoke

```bash
python3 -m minerva_kernel.eval_smoke
```

Expected result:

```text
Cases: 5/5 passed, 0 failed
Safe Recovery Decision Rate: 5/5 (100.0%)
```

## 4. Try The GitHub Action

After the repository is public, another repository can use Minerva as a
diagnostic CI step:

```yaml
- name: Diagnose failed CI log
  if: ${{ failure() }}
  uses: smithpeter/minerva-ai-kernel@v0.1.0
  with:
    log-path: build.log
    job-name: tests
```

The action writes a Minerva diagnosis to the GitHub step summary. It is
report-only by default and does not override the original job outcome.
