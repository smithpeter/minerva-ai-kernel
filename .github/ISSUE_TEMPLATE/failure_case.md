---
name: Failure case
about: Submit a redacted command, CI, tool, build, test, network, or model failure for Minerva
title: "Failure case: "
labels: "failure-case"
assignees: ""
---

## Redaction Confirmation

- [ ] I removed secrets, credentials, tokens, cookies, private keys, private logs, full environment dumps, proprietary source, and customer data.
- [ ] I replaced sensitive identifiers with placeholders such as `<REDACTED_SECRET>`, `<REDACTED_ID>`, `<REDACTED_HOST>`, or `<REDACTED_PATH>`.

## Required Fields

```text
title:
failure_area:
trigger:
exit_code:
observed_signal:
expected_failure_label:
safe_next_action:
risk_notes:
redaction_statement:
reproduction_notes:
```

## Minimal Redacted Signal

Paste only the smallest redacted stderr/stdout/log snippet needed to understand
the failure.

```text

```

## What Not To Submit

Do not submit secrets, raw unredacted logs, full environment dumps, proprietary
source code, private customer data, or private infrastructure details.

See the full guide: [Failure Case Contributions](../../docs/failure-case-contributions.md).
