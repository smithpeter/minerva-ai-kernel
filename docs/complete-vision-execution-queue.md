# Complete Vision Execution Queue

Date: 2026-05-10

## Goal

Advance the complete Minerva vision:

```text
CPU small model
  + eval data loop
  + AIOps / CI ecosystem
  + stable release operations
```

The local AI-team queue now resumes with T51-T58. Each task card includes a
Plan-Eng Review block so workers must reason about scope, existing assets,
failure modes, tests, and parallelization before editing files.

## Queue Summary

| Task | Lane | Title | Primary Result |
| --- | --- | --- | --- |
| T51 | Eval | Expand CPU eval corpus to contract-ready coverage | Broader `evals/cpu_model_cases.jsonl` with category mix and fallback cases |
| T52 | Eval / Data | Add eval data loop artifact schema | Run records can become reviewable corpus candidates |
| T53 | Research / Model | Add local CPU candidate runbook and report artifacts | Repeatable Ollama/GGUF candidate evidence path |
| T54 | Integration / CI | Add CI log analysis command design and first implementation | CLI entry for CI logs/JUnit-style artifacts |
| T55 | Kernel / Daemon | Extend minervad with local diagnosis API | AIOps embedding surface beyond health check |
| T56 | Security / Ops | Add AIOps taxonomy and safe action mapping plan | Ops-specific labels/actions without auto-repair |
| T57 | Release | Add stable release operations dashboard | Release readiness rollup includes Plan-Eng and eval status |
| T58 | Docs / Ecosystem | Add ecosystem adapter/event reporting guide | Platforms can embed Minerva without guessing contracts |

## Dependency Shape

```text
T51 -> T53
T51 -> T52
T52 -> T57
T54 -> T58
T55 -> T58
T56 -> T54/T55
T57 waits for verification evidence from T51-T56
```

T51, T52, T54, T55, and T56 can start in parallel if workers respect allowed
file boundaries. T53 should wait for T51's expanded corpus. T57 should be last.

## Operating Rule

Workers must use [`docs/ai-team-task-template.md`](ai-team-task-template.md)
for any additional tasks they create. Substantial changes are not done until:

```text
Plan-Eng Review block exists
no critical failure-mode gap remains
listed tests/evals pass
Output records what changed and what remains
```
