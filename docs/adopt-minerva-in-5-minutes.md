# Adopt Minerva in 5 minutes

This runbook gets an external GitHub repository from no Minerva integration to
a visible GitHub Actions summary and downloadable artifact. It does not require
private credentials, paid services, or a remote LLM.

## Install line

Add Minerva to a GitHub Actions job with this action step:

```yaml
- name: Observe command with Minerva
  uses: smithpeter/minerva-action@v0
```

That `uses:` line is the install line for CI. The action runs the observed
command, renders a markdown summary, and publishes a redacted artifact.

## Time to first observation: < 5 min

1. Create `.github/workflows/minerva-first-observation.yml`.
2. Paste the workflow below.
3. Open the Actions tab and run **Minerva first observation** with
   **Run workflow**, or open a pull request.
4. Open the completed run summary and confirm the Minerva markdown appears.
5. Download the `minerva-ci-evidence` artifact from the same run.

The first demo command intentionally exits with status `1`. That proves Minerva
does not hide the observed command result while still publishing diagnostic
evidence.

## Sample workflow yml

```yaml
name: Minerva first observation

on:
  workflow_dispatch:
  pull_request:

jobs:
  observe:
    runs-on: ubuntu-latest
    permissions:
      contents: read

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Observe controlled failure with Minerva
        uses: smithpeter/minerva-action@v0
        with:
          command: >-
            python3 -c "import minerva_demo_missing"
          summary-path: minerva-ci-summary.md
          artifact-name: minerva-ci-evidence
          redaction-mode: strict
```

After the first artifact is visible, replace the controlled failure with the
real CI command for the repository, for example:

```yaml
          command: python3 -m unittest discover -s tests
```

Put project setup steps before the Minerva step when the real command needs
dependencies, generated files, or a specific runtime.

## Expected output

The workflow run should fail on the controlled first observation because the
observed Python import fails. The GitHub Actions summary should still contain a
Minerva markdown section with the same shape as the checked-in example summary:

```markdown
# Minerva CI Summary

Status: failed, policy allowed diagnostic action

| Field | Value |
| --- | --- |
| Command | `python3 -c "import minerva_demo_missing"` |
| Exit code | `1` |

## Failure Interpretation

| Field | Value |
| --- | --- |
| Failure | `missing_dependency` |
| Diagnostic action | `inspect_dependencies` |
| Risk | `low` |

## Safety Gate

| Check | Result |
| --- | --- |
| Auto-repair | disabled |
| Artifact redacted | yes |
| GitHub API credentials | not required |
```

The run should also expose an artifact named `minerva-ci-evidence`. Keep that
artifact redacted; do not upload full raw logs, environment dumps, credential
files, provider prompts, or secret values.

For the static output shape used by Minerva, see the
[markdown summary example](../examples/minerva-ci-summary.md) and
[JSON artifact example](../examples/minerva-ci-run-artifact.json).

## Where to look in Actions UI

Open the repository on GitHub, then go to:

1. **Actions**.
2. **Minerva first observation**.
3. The latest workflow run for the branch or pull request.
4. **Summary** for the rendered markdown job summary.
5. **Artifacts** for `minerva-ci-evidence`.

The screenshot below is a redacted GitHub Actions run showing the Minerva
markdown summary rendered from `$GITHUB_STEP_SUMMARY`.

![Redacted GitHub Actions run][actions-summary-screenshot]

## Troubleshooting

1. `Unable to resolve action smithpeter/minerva-action@v0`

   Fix: check the `uses:` line for typos and keep the tag pinned to `@v0`
   until a newer public tag is documented.

2. The job fails but no summary appears

   Fix: confirm the Minerva step is the step that observes the command, and
   keep `summary-path: minerva-ci-summary.md`.

3. No artifact appears

   Fix: keep `artifact-name: minerva-ci-evidence`. If a later step deletes
   files, move that cleanup after artifact upload.

4. The observed command is not found

   Fix: add setup steps before Minerva, such as `actions/setup-python`,
   dependency install, or build preparation.

5. The summary contains less diagnosis than expected

   Fix: use a command that emits bounded stderr/stdout evidence, and keep
   `redaction-mode: strict` so secrets stay out of summaries and artifacts.

## Safety notes

- Minerva is diagnostic only in this workflow.
- The action exits with the observed command status.
- No GitHub API token, private credential, paid model, or remote LLM is needed.
- Redacted summaries and artifacts are intended for CI evidence, not repair.

[actions-summary-screenshot]: screenshots/minerva-actions-summary-redacted.png
