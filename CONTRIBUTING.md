# Contributing

Minerva is issue-driven.

Every contribution should include at least one of:

- unit test
- eval case
- CLI demo
- documentation update
- benchmark result
- security test

## Good First Contributions

- Add failure cases.
- Add taxonomy labels.
- Add safe action mappings.
- Add CI examples.
- Add dangerous action tests.
- Improve docs.

## Safety

Do not add behavior that allows the model to execute arbitrary shell commands.

Core rule:

```text
LLM interprets. Policy authorizes. Executor acts.
```

