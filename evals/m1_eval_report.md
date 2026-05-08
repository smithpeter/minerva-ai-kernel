# M1 Eval Report

Generated deterministically from local fixtures by `python3 -m minerva_kernel.eval_report --format markdown`.

## Corpus Summary

The default failure corpus contains 112 validated cases across 12 required categories.

Target: 15 cases per required category.
Total gap to target: 68 cases.

| Category | Count | Target | Remaining gap |
| --- | ---: | ---: | ---: |
| `python` | 9 | 15 | 6 |
| `shell-cli` | 9 | 15 | 6 |
| `git` | 10 | 15 | 5 |
| `npm-node` | 9 | 15 | 6 |
| `docker-build` | 9 | 15 | 6 |
| `dns-network` | 9 | 15 | 6 |
| `permission` | 9 | 15 | 6 |
| `timeout` | 9 | 15 | 6 |
| `ci` | 10 | 15 | 5 |
| `model-api` | 10 | 15 | 5 |
| `schema-json` | 10 | 15 | 5 |
| `secret-redaction` | 9 | 15 | 6 |

## M1 Metrics

| Metric | Result | Notes |
| --- | ---: | --- |
| JSON validity | 5/5 smoke decisions and 112/112 corpus cases valid | Smoke decisions round-trip through `decision.v0`; corpus cases load through `load_failure_cases()`. |
| Failure label accuracy | 5/5 (100.0%) | Smoke decision failure labels matched expected labels. |
| Safe recovery decision rate | 5/5 (100.0%) | Smoke decisions matched expected safe actions and read-only policy allowed each action. |
| Escalation quality | 5/5 (100.0%) | False positives: 0; false negatives: 0; expected escalations: 0. |
| Dangerous action rate | 0/117 (0.0%) | Smoke: 0/5; corpus: 0/112. |

## Remaining Gaps

- Failure corpus needs 68 more cases to reach the per-category target.
- Add positive escalation fixtures for ambiguous, high-risk, or insufficient-evidence cases.
- Keep dangerous-action checks at zero while expanding the corpus.
