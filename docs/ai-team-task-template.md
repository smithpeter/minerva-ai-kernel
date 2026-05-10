# AI Team Task Template

Use this template for new local task cards in `.tasks/`.

````markdown
# Task: <short imperative title>

- Status: pending
- GitHub Issue: https://github.com/smithpeter/minerva-ai-kernel/issues/<number>
- Owner Lane: <Product / Kernel / Eval / Integration / Security / Docs / Release / Ops>
- Allowed Files: `<path-or-prefix>`, `<path-or-prefix>`

## Goal

State the user-visible or project-visible outcome.

## Plan-Eng Review

### Scope Challenge
- Accepted scope:
- Reduced or deferred scope:

### What Already Exists
- Existing code/docs reused:
- Existing tests/evals reused:

### NOT In Scope
- Deferred:

### Architecture / Flow
```text
input
  -> component
  -> policy/eval/check
  -> persisted output
```

### State / Decision Diagram
```text
[pending] -> [in_progress] -> [verified] -> [done]
                  |               |
                  v               v
               [blocked]       [needs fix]
````

### Failure Modes
| Failure mode | Covered by test/eval | Error handling | User-visible outcome |
| --- | --- | --- | --- |
| <realistic failure> | yes/no | yes/no | clear/silent |

### Test / Eval Plan
- Required command:
- Additional focused check:

### Parallelization
- Sequential because:
- Parallel lanes, if any:

### Review Readiness
- Diff review focus:
- Release or docs impact:

## Acceptance Criteria

- Concrete completion criterion.
- Concrete completion criterion.
- No critical Plan-Eng failure-mode gap remains open.

## Non-Goals

- Deferred work.
- Explicit safety or scope boundary.

## Test / Eval

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
```

## Output

Filled by the worker before setting `Status: done`.
```

For trivial documentation-only tasks, keep the Plan-Eng Review concise, but do
not delete it. State why the lightweight version is enough and how the change
will be verified.
