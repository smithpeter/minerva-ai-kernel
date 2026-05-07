# Research Brief

## Problem

Software systems increasingly need to react to complex runtime states: code errors, process failures, missing dependencies, network problems, hardware limitations, tool failures, and changing APIs. Traditional schedulers use static rules. This project explores a scheduler that uses an LLM as a runtime reasoning component.

## Core Requirement

Code should always be able to call an LLM through a stable interface.

The system should always try to keep at least one LLM usable:

- tiny local LLM
- stronger local LLM
- remote LLM
- human escalation

## Non-Goal

This project does not assume that the smallest local LLM can solve all problems. Its job is to:

- classify failures
- summarize observations
- choose safe next actions
- decide whether to escalate
- maintain continuity when larger models or networks are unavailable

## Hypothesis

A small code-capable LLM, constrained to structured outputs and a limited action space, can serve as a useful local scheduling kernel for many development and operations tasks.

## Expected Outcome

A working prototype that can:

1. Run a command or tool.
2. Observe stdout, stderr, exit code, and environment metadata.
3. Ask a local LLM for the next action.
4. Validate the action against policy.
5. Execute the action or escalate.
6. Store outcomes for future routing decisions.
