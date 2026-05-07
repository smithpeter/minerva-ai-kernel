# Experiment Plan

## Phase 1: Local Model Availability

Test:

- Ollama installed
- `qwen2.5-coder:0.5b-instruct` available
- OpenAI-compatible local endpoint works
- latency for short prompts
- JSON reliability

## Phase 2: Error Classification

Feed the model fixed examples:

- Python syntax error
- missing module
- command not found
- permission denied
- DNS failure
- connection timeout
- port already in use

Measure:

- diagnosis accuracy
- valid JSON rate
- action safety
- escalation correctness

## Phase 3: Closed Loop

Run small workflows:

- failing shell command
- missing package
- bad URL
- simple test failure

Measure:

- number of steps to success
- wrong actions
- unnecessary escalations
- repeated failures

## Phase 4: Model Tiering

Compare:

- Qwen2.5-Coder 0.5B
- Qwen3 0.6B
- Qwen2.5-Coder 1.5B
- remote strong model

Measure:

- cost
- latency
- correctness
- escalation rate

## Phase 5: Scheduler Memory

Add memory of outcomes:

- command failed before
- model produced invalid JSON before
- network is currently unavailable
- a tool is missing

Measure whether memory reduces repeated bad actions.
