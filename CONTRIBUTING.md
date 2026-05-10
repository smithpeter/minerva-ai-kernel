# Contributing

Minerva is issue-driven.

Project maintainer contact: `maintainers@minervakernel.com`.

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

## Failure Cases

Failure cases are welcome when they are small, redacted, and reviewable. Use
the [failure case contribution guide](docs/failure-case-contributions.md) before
opening an issue or PR.

Do not submit secrets, raw unredacted logs, full environment dumps, proprietary
source, or private customer data.

## Safety

Do not add behavior that allows the model to execute arbitrary shell commands.

Core rule:

```text
LLM interprets. Policy authorizes. Executor acts.
```
