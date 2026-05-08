# Minerva CI Summary

Status: failed, policy allowed diagnostic action

| Field | Value |
| --- | --- |
| Command | `python3 -m unittest discover -s tests` |
| Working directory | `/workspace/minerva-ai-kernel` |
| Exit code | `1` |
| Duration | `931 ms` |
| Run record | `.minerva/runs/20260508T120000Z-a1b2c3d4.json` |

## Failure Interpretation

| Field | Value |
| --- | --- |
| Failure | `missing_dependency` |
| Diagnostic action | `inspect_dependencies` |
| Confidence | `0.82` |
| Risk | `low` |
| Escalation requested | `false` |

Minerva classified the failure from bounded stderr evidence and proposed a
read-only diagnostic action. CI should not execute this action automatically.

## Safety Gate

| Check | Result |
| --- | --- |
| Auto-repair | disabled |
| Model input redacted | yes |
| Artifact redacted | yes |
| Policy decision | allowed |
| Policy reason | `allowed by read-only policy` |
| GitHub API credentials | not required |

## Evidence Excerpts

stdout tail:

```text
Using Authorization: Bearer [REDACTED:bearer_token]
```

stderr tail:

```text
ModuleNotFoundError: No module named 'minerva_kernel'
```

Redactions:

```text
count=1 types=bearer_token
```
