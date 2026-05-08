# Model Strategy

## Goal

Find the smallest local model that can reliably perform scheduler tasks:

- classify errors
- inspect command output
- identify missing dependencies
- recognize network failures
- suggest safe next actions
- decide when to escalate

## Candidate Tiers

### L0: Tiny Local Code Controller

Recommended first model:

```text
qwen2.5-coder:0.5b-instruct
```

Why:

- small enough to keep resident
- code-specific
- useful for shell output, stack traces, and simple fixes
- available through Ollama

Example:

```bash
ollama run qwen2.5-coder:0.5b-instruct
```

## Minimum Local Provider Path

The minimum provider path is CPU local and OpenAI-compatible through Ollama.
Remote models are not required for this path.

Small candidate:

```text
qwen2.5-coder:0.5b-instruct
```

Default Minerva provider settings:

```text
base_url: http://localhost:11434/v1/chat/completions
model: qwen2.5-coder:0.5b-instruct
timeout: 20 seconds
```

Setup:

```bash
ollama serve
ollama pull qwen2.5-coder:0.5b-instruct
```

Verify the OpenAI-compatible chat endpoint:

```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -d '{
    "model": "qwen2.5-coder:0.5b-instruct",
    "messages": [
      {
        "role": "system",
        "content": "Return only valid JSON."
      },
      {
        "role": "user",
        "content": "Return {\"failure\":\"smoke\",\"action\":\"stop\",\"confidence\":1,\"risk\":\"low\",\"escalate\":false,\"evidence\":[\"smoke\"]}"
      }
    ],
    "temperature": 0,
    "response_format": {"type": "json_object"}
  }' | python3 -m json.tool
```

Run Minerva against the same local endpoint:

```bash
python3 -m pip install --no-deps .
minerva observe -- python3 -c 'import sys; print("ImportError: No module named yaml", file=sys.stderr); sys.exit(3)'
```

The current router already points to this path when no provider is injected:

```python
from minerva_kernel.router import LocalLLMRouter

decision = LocalLLMRouter().propose(messages)
```

### No-Provider Fallback

If the local endpoint is not running, refuses the connection, or times out,
`LocalOpenAICompatibleProvider` returns a structured decision instead of calling
a remote model:

```json
{
  "schema_version": "decision.v0",
  "failure": "local_llm_unavailable",
  "action": "ask_bigger_llm",
  "confidence": 1.0,
  "risk": "low",
  "escalate": true,
  "evidence": ["local LLM request failed"]
}
```

In the CLI path, Minerva still captures and saves the observation/run record.
The read-only policy blocks `ask_bigger_llm`, so the minimum path is safe even
without a model:

```text
Failure: local_llm_unavailable
Action: ask_bigger_llm
Policy decision: blocked
Policy decision reason: action is not read-only: ask_bigger_llm
```

Remote models are optional L3 escalation targets. They must remain outside the
minimum path: no automatic remote fallback, no remote key requirement, and no
failure to run the local observer when remote access is unavailable.

### L1: Tiny General Agent Controller

Recommended model:

```text
Qwen3-0.6B-GGUF
```

Why:

- small local model
- better general reasoning than a pure code model
- supports thinking/no-thinking modes
- suitable for tool-routing experiments

### L2: Stronger Local Model

Examples:

- Qwen2.5-Coder 1.5B / 3B / 7B
- Qwen3 1.7B / 4B / 8B

Use for:

- ambiguous failures
- multi-file code analysis
- deeper planning
- risky proposed edits

### L3: Remote Strong Model

Use when:

- local confidence is low
- context is too large
- task requires stronger reasoning
- repeated local attempts fail

## Routing Rules

Start with the cheapest model that is likely to work.

Escalate when:

- confidence is below threshold
- JSON output is invalid twice
- the action fails repeatedly
- the task touches sensitive files
- the task requires nontrivial code modification
- the model says escalation is needed

## Important Constraint

The tiny model should not be treated as an autonomous engineer. It is a classifier, router, summarizer, and first-pass controller.
