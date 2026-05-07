# Architecture

## High-Level Shape

```text
Application Code
      |
      v
LLM Scheduler API
      |
      v
Router -> Model Health -> Model Tier Selection
      |
      v
Planner -> Structured Prompt -> LLM
      |
      v
Action Validator -> Policy Engine -> Executor
      |
      v
Observation Store -> Next Loop
```

## Components

### Scheduler API

The only interface application code uses. It hides model provider differences.

### Router

Chooses which model to use based on:

- availability
- latency
- task type
- context length
- previous failures
- confidence requirements
- network status

### Planner

Turns raw environment observations into compact prompts:

- command
- stdout
- stderr
- exit code
- working directory
- file context
- resource state
- recent history

### LLM

Returns only structured actions. Natural language can be stored as explanation, but it is not the execution interface.

### Policy Engine

Rejects unsafe, impossible, or low-confidence actions.

Examples:

- disallow destructive shell commands unless explicitly approved
- disallow network access in offline mode
- require escalation for credential access
- require stronger model for ambiguous edits

### Executor

Runs allowed actions:

- local command
- inspect file
- search local code
- retry with modified parameters
- call stronger model
- ask user

### Observation Store

Stores compact records:

- what happened
- what action was chosen
- whether it worked
- model used
- latency
- confidence

This becomes the scheduler's operational memory.
