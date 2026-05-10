# GitHub Action

Minerva can run as a diagnostic GitHub Action after a job creates a local log
file.

```yaml
- name: Run tests
  id: tests
  shell: bash
  run: |
    set -o pipefail
    python3 -m unittest discover -s tests 2>&1 | tee build.log

- name: Diagnose failure with Minerva
  if: ${{ failure() }}
  uses: smithpeter/minerva-ai-kernel@v0.1.0
  with:
    log-path: build.log
    job-name: tests
```

Inputs:

| Input | Required | Default | Meaning |
| --- | --- | --- | --- |
| `log-path` | yes | none | Local log file path to diagnose. |
| `job-name` | no | `ci-log` | Job label recorded in observation runtime metadata. |
| `tail-chars` | no | `12000` | Maximum tail characters included in the observation. |
| `fail-on-policy-block` | no | `false` | If true, policy-blocked diagnoses make the action fail. |

Safety boundaries:

- The action installs and runs Minerva locally in the workflow workspace.
- It does not call remote models.
- It does not execute Minerva-proposed actions.
- It writes a bounded diagnosis to `$GITHUB_STEP_SUMMARY`.
- The original job should remain the source of pass/fail truth.
