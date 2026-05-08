# M1 Eval Report

Report date: 2026-05-08

## Corpus Summary

The default failure corpus now contains 112 synthetic, schema-validated cases,
up from the M0 slice of 100. Each required category gained one case while
preserving unique IDs, observation schema validation, secret-redaction
expectations, and read-only safe expected actions.

| Category | M0 count | M1 count | Target | Remaining gap |
| --- | ---: | ---: | ---: | ---: |
| `python` | 8 | 9 | 15 | 6 |
| `shell-cli` | 8 | 9 | 15 | 6 |
| `git` | 9 | 10 | 15 | 5 |
| `npm-node` | 8 | 9 | 15 | 6 |
| `docker-build` | 8 | 9 | 15 | 6 |
| `dns-network` | 8 | 9 | 15 | 6 |
| `permission` | 8 | 9 | 15 | 6 |
| `timeout` | 8 | 9 | 15 | 6 |
| `ci` | 9 | 10 | 15 | 5 |
| `model-api` | 9 | 10 | 15 | 5 |
| `schema-json` | 9 | 10 | 15 | 5 |
| `secret-redaction` | 8 | 9 | 15 | 6 |

Total gap to the documented 15-case target: 68 cases.

## M1 Metrics

Metrics are computed from the deterministic smoke fixture and the validated
default failure corpus on 2026-05-08.

| Metric | Result | Notes |
| --- | ---: | --- |
| JSON validity | 5/5 smoke decisions and 112/112 corpus cases valid | Smoke decisions round-trip through `decision.v0`; corpus cases load through `load_failure_cases()`. |
| Failure label accuracy | 5/5 (100.0%) | Smoke decision failure labels matched expected labels. |
| Safe recovery decision rate | 5/5 (100.0%) | Smoke decisions matched expected safe actions and read-only policy allowed each action. |
| Escalation quality | 5/5 (100.0%) no false escalations | Current smoke fixture only covers cases expected to stay local; positive escalation cases remain a gap. |
| Dangerous action rate | 0/5 smoke decisions and 0/112 corpus expected actions | No smoke decision or corpus expected action used a dangerous or write-capable action. |

Smoke command:

```bash
python3 -m minerva_kernel.eval_smoke
```

Observed output summary:

```text
Cases: 5/5 passed, 0 failed
Safe Recovery Decision Rate: 5/5 (100.0%)
```

## Remaining Gaps

- Grow the 68 remaining category examples needed to reach 15 cases per
  required category.
- Add positive escalation fixtures for ambiguous, high-risk, or insufficient
  evidence cases so escalation quality measures both recall and false positive
  rate.
- Add review-labeled ambiguous cases where multiple failures appear together,
  especially auth plus network, dependency plus platform, and provider schema
  plus model runtime errors.
- Keep secret-redaction cases synthetic or fully sanitized, with human review
  before admitting any log-derived examples.
- Keep dangerous-action checks in policy fixtures and eval reports; failure
  corpus expected actions should remain read-only safe actions.
