# Failure Case Contributions

Failure cases are the easiest way to improve Minerva. A good case gives enough
signal to classify the failure and choose a safe next action, without exposing
private systems, secrets, or proprietary code.

Submit a failure case when you can share a small, redacted example of a command,
CI job, tool call, build, test, network request, model call, or deployment step
that failed in a useful way.

## Required Fields

Every failure case should include:

- `title`: short human-readable summary.
- `failure_area`: one domain such as `python`, `shell`, `git`, `docker`, `npm`, `ci`, `network`, `model_api`, or `schema`.
- `trigger`: the command, tool action, CI step, or operation that failed.
- `exit_code`: process exit code when available, or `unknown`.
- `observed_signal`: the smallest redacted stderr/stdout/log snippet that shows the failure.
- `expected_failure_label`: the best concise label, such as `missing_dependency`, `dns_failure`, `permission_denied`, `test_assertion_failure`, `rate_limited`, or `json_schema_failure`.
- `safe_next_action`: one bounded diagnostic or repair step that should be safe to suggest.
- `risk_notes`: anything Minerva should avoid doing automatically.
- `redaction_statement`: confirmation that secrets, private logs, environment dumps, and proprietary source have been removed.
- `reproduction_notes`: minimal steps or context needed to understand the failure.

Use `unknown` when a field is not available. Do not invent data.

## Redaction Expectations

Before submitting, replace sensitive values with stable placeholders:

- API tokens, passwords, private keys, session cookies: `<REDACTED_SECRET>`.
- Personal names, emails, account IDs, tenant IDs: `<REDACTED_ID>`.
- Internal hostnames, private IPs, repository URLs: `<REDACTED_HOST>` or `<REDACTED_REPO>`.
- Proprietary paths or package names: `<REDACTED_PATH>` or `<REDACTED_PACKAGE>`.
- Customer data, payloads, database rows: `<REDACTED_DATA>`.

Keep the error shape intact. For example, preserve `ModuleNotFoundError`,
`ECONNREFUSED`, `No space left on device`, HTTP status codes, stack-frame
function names you own and can share, and one or two relevant lines around the
failure. Prefer short snippets over full logs.

## What Not To Submit

Do not submit:

- Secrets, credentials, tokens, cookies, private keys, or signing material.
- Private logs or raw unredacted logs.
- Full environment dumps, full CI logs, or full process tables.
- Proprietary source code or private customer data.
- Internal infrastructure names that would expose private topology.
- Data that your employer, customer, or license does not allow you to share.

If redaction removes too much context, submit the high-level failure shape and
state what was redacted.

## Good Example

```text
title: Python dependency missing in clean CI image
failure_area: python
trigger: python3 -m unittest discover -s tests
exit_code: 1
observed_signal:
  ImportError: Failed to import test module: test_observer
  ModuleNotFoundError: No module named '<REDACTED_PACKAGE>'
expected_failure_label: missing_dependency
safe_next_action: Check whether the package is declared in project dependencies before rerunning tests.
risk_notes: Do not install packages globally or modify lockfiles without review.
redaction_statement: Package name and repo path were redacted; no secrets or private logs included.
reproduction_notes: Happens in a clean Linux CI image after checkout and dependency install.
```

## Poor Example

```text
Here is my full CI log and env dump.
AWS_SECRET_ACCESS_KEY=...
DATABASE_URL=...
```

This is not acceptable because it includes secrets and too much unrelated
private context.

## Review Checklist

Reviewers should accept a failure case only when:

- The failure can be understood from a small redacted signal.
- Required fields are present, or unavailable fields are marked `unknown`.
- The expected label is concise and useful for grouping similar failures.
- The safe next action is diagnostic or narrowly bounded.
- Risk notes name actions that should require human approval.
- No secrets, private logs, full env dumps, proprietary source, or customer data are present.
- The case improves coverage of a real Minerva failure area.

When in doubt, ask the contributor to remove more data and keep only the failure
shape.
