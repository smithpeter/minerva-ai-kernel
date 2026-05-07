# Success Principles

Date: 2026-05-08

## Core Success Claim

Minerva succeeds only if it proves:

```text
A sub-500M CPU model can translate runtime failure state into safe structured action under strict constraints.
```

Everything else is secondary.

## Five Foundations

Traditional interpreters need:

- syntax
- instruction set
- runtime
- error handling
- standard library

Minerva needs:

- Observation Schema
- Minerva Instruction Set
- Policy Runtime
- Failure Taxonomy
- Safe Action Library

## Observation Schema

The input to Minerva must be standardized.

It should include:

- command
- exit code
- stdout
- stderr
- cwd
- available tools
- resource state
- policy state
- recent history

This is Minerva's equivalent of source syntax.

## Minerva Instruction Set

The output must be finite and stable.

Initial instructions:

```text
stop
retry
check_dns
check_network
check_port
inspect_file
inspect_dependencies
search_local
check_command_exists
check_permissions
ask_bigger_llm
ask_user
```

This is Minerva's equivalent of bytecode/instructions.

## Policy Runtime

The model must not execute directly.

Required flow:

```text
LLM proposes -> Policy validates -> Executor acts -> Feedback records
```

Policy must be a hard boundary.

## Failure Taxonomy

The taxonomy gives the model a bounded semantic world.

Examples:

- dns_failure
- network_timeout
- permission_denied
- missing_dependency
- command_not_found
- port_in_use
- json_parse_error
- model_unavailable
- context_overflow
- unsafe_action

## Safe Action Library

Tiny models should choose action labels, not arbitrary commands.

Example:

```text
check_dns -> dig +short <host>
check_port -> lsof -i :<port>
inspect_dependencies -> inspect pyproject.toml/package.json
```

## Self-Improvement Boundary

Allowed:

- update failure corpus
- tune routing thresholds
- improve taxonomy
- improve policy packs
- generate distillation data
- train smaller adapters

Not allowed by default:

- self-authorize new permissions
- bypass policy
- arbitrary shell execution
- modify core runtime silently
- expand filesystem or network access silently

Principle:

```text
self-improving through evidence, not self-authorizing through autonomy
```

Chinese:

```text
通过证据自我改进，而不是通过自治自我授权。
```

## First Proof

The first proof should be:

```bash
minerva observe -- <command>
```

Then:

```text
run command
capture stdout/stderr/exit_code
build observation
call CPU sub-500M model
return structured decision
policy-check action
record result
```

## Avoid Failure Modes

Avoid:

- becoming a general agent framework
- starting with Rust before the research works
- training before eval
- free-form command generation
- relying on remote models for the minimum function
- overclaiming autonomy
- skipping the corpus

